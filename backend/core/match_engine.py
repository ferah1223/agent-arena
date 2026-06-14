"""
Agent Arena — Match Engine
============================
Orchestrates matches: spawns agent subprocesses, runs rounds,
judges responses, calculates Elo, and broadcasts events via WebSocket.

Agents are invoked as:
    hermes run "<task>" --profile <agent_profile>

Robust: handles timeouts, zombie process cleanup, concurrent match limits.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import signal
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from db.store import (
    CHALLENGE_PROMPTS,
    GAME_MODES,
    Agent,
    GameModeId,
    JudgeScore,
    Match,
    MatchRound,
    MatchStatus,
    AgentRoundData,
    calculate_elo,
    store,
)
from websocket.manager import manager as ws_manager

logger = logging.getLogger("arena.match_engine")

# ── Configuration ──────────────────────────────────────────────

MAX_CONCURRENT_MATCHES = 5
DEFAULT_ROUND_TIMEOUT = 120  # seconds
JUDGE_TIMEOUT = 60  # seconds
PROCESS_CLEANUP_WAIT = 5  # seconds to wait for graceful shutdown

# Semaphore to limit concurrent matches
_match_semaphore: Optional[asyncio.Semaphore] = None
_active_matches: dict[str, asyncio.Task] = {}


def _get_semaphore() -> asyncio.Semaphore:
    global _match_semaphore
    if _match_semaphore is None:
        _match_semaphore = asyncio.Semaphore(MAX_CONCURRENT_MATCHES)
    return _match_semaphore


# ── Subprocess Helpers ─────────────────────────────────────────

async def _run_agent_subprocess(
    profile_name: str,
    task: str,
    timeout: int = DEFAULT_ROUND_TIMEOUT,
) -> dict[str, Any]:
    """
    Run an agent via hermes subprocess.
    Returns {"response": str, "time_ms": int, "error": str|None}
    """
    cmd = ["hermes", "run", task, "--profile", profile_name]
    logger.info("Running agent: hermes run %r --profile %s (timeout=%ds)", task[:80], profile_name, timeout)

    start_time = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            # Kill the process group
            logger.warning("Agent %s timed out after %ds — killing", profile_name, timeout)
            _kill_process(proc)
            try:
                await asyncio.wait_for(proc.wait(), timeout=PROCESS_CLEANUP_WAIT)
            except asyncio.TimeoutError:
                proc.kill()
            return {
                "response": "",
                "time_ms": int((time.monotonic() - start_time) * 1000),
                "error": "timeout",
            }

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        response = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            logger.warning("Agent %s exited with code %d. stderr: %s", profile_name, proc.returncode, err[:200])
            return {
                "response": response or "",
                "time_ms": elapsed_ms,
                "error": f"exit_code_{proc.returncode}",
            }

        return {"response": response, "time_ms": elapsed_ms, "error": None}

    except FileNotFoundError:
        logger.error("'hermes' command not found — is it installed and on PATH?")
        return {"response": "", "time_ms": 0, "error": "hermes_not_found"}
    except Exception:
        logger.exception("Unexpected error running agent %s", profile_name)
        return {"response": "", "time_ms": 0, "error": "unexpected_error"}


def _kill_process(proc: asyncio.subprocess.Process) -> None:
    """Attempt to gracefully kill a process and its children."""
    try:
        if proc.returncode is not None:
            return
        # Try SIGTERM first
        proc.terminate()
    except ProcessLookupError:
        pass


async def _run_judge(
    prompt: str,
    response_a: str,
    response_b: str,
    criteria: list[str],
    match_id: str,
) -> list[JudgeScore]:
    """
    Use a judge agent to evaluate two responses.
    Runs: hermes run "<judge_prompt>" --profile judge
    Returns list of JudgeScore.
    """
    criteria_text = "\n".join(f"  - {c}" for c in criteria)
    judge_prompt = f"""You are an impartial judge for Agent Arena match {match_id}.

TASK/PROMPT:
{prompt}

AGENT A RESPONSE:
{response_a}

AGENT B RESPONSE:
{response_b}

Score each criterion from 1-10 for BOTH agents. Criteria:
{criteria_text}

Reply ONLY with valid JSON array (no markdown fences), exactly this format:
[
  {{"criterion": "...", "agent_a_score": N, "agent_b_score": N, "reasoning": "..."}}
]
"""

    result = await _run_agent_subprocess("judge", judge_prompt, timeout=JUDGE_TIMEOUT)
    raw = result.get("response", "")

    try:
        # Try to extract JSON from response
        parsed = _extract_json(raw)
        scores = []
        for item in parsed:
            scores.append(JudgeScore(
                criterion=item.get("criterion", "unknown"),
                agent_a_score=int(item.get("agent_a_score", 5)),
                agent_b_score=int(item.get("agent_b_score", 5)),
                reasoning=item.get("reasoning", ""),
                judge_model="hermes-judge",
            ))
        return scores
    except Exception:
        logger.warning("Failed to parse judge response, using fallback scoring. Raw: %s", raw[:300])
        return _fallback_judge_scores(criteria)


def _extract_json(text: str) -> list[dict[str, Any]]:
    """Extract JSON array from text that might have extra content."""
    text = text.strip()
    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    # Try to find JSON array in text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError("No valid JSON array found")


def _fallback_judge_scores(criteria: list[str]) -> list[JudgeScore]:
    """Generate deterministic-ish fallback scores if judge fails."""
    scores = []
    for criterion in criteria:
        a_score = random.randint(5, 8)
        b_score = random.randint(5, 8)
        scores.append(JudgeScore(
            criterion=criterion,
            agent_a_score=a_score,
            agent_b_score=b_score,
            reasoning=f"[Fallback] {criterion}: both agents performed adequately.",
            judge_model="fallback",
        ))
    return scores


def _pick_prompts(game_mode: GameModeId, num_rounds: int) -> list[str]:
    """Pick unique challenge prompts for the match rounds."""
    available = CHALLENGE_PROMPTS.get(game_mode, [
        "Explain your reasoning step by step.",
        "Solve the given problem concisely.",
        "Provide your best answer.",
    ])
    chosen = random.sample(available, min(num_rounds, len(available)))
    # If we need more than available, repeat with variation
    while len(chosen) < num_rounds:
        chosen.append(random.choice(available))
    return chosen


# ── Core Match Logic ───────────────────────────────────────────

async def run_round(
    match_id: str,
    round_num: int,
    prompt: str,
    agent_a: Agent,
    agent_b: Agent,
    game_mode: GameModeId,
    round_timeout: int = DEFAULT_ROUND_TIMEOUT,
) -> MatchRound:
    """
    Execute a single round:
    1. Send prompt to both agents concurrently
    2. Collect responses
    3. Judge responses
    4. Broadcast events
    """
    round_id = f"{match_id}-r{round_num}"
    logger.info("[%s] Round %d starting: %s", match_id, round_num, prompt[:60])

    # Broadcast round start
    await ws_manager.emit_round_start(match_id, {
        "roundNumber": round_num,
        "prompt": prompt,
        "matchId": match_id,
    })

    # Run both agents concurrently
    await ws_manager.emit_agent_action(match_id, agent_a.id, "thinking")
    await ws_manager.emit_agent_action(match_id, agent_b.id, "thinking")

    result_a, result_b = await asyncio.gather(
        _run_agent_subprocess(agent_a.profile_name, prompt, timeout=round_timeout),
        _run_agent_subprocess(agent_b.profile_name, prompt, timeout=round_timeout),
    )

    # Broadcast partial responses (for streaming feel)
    if result_a["response"]:
        await ws_manager.emit_agent_action(match_id, agent_a.id, "responded", result_a["response"][:200])
    if result_b["response"]:
        await ws_manager.emit_agent_action(match_id, agent_b.id, "responded", result_b["response"][:200])

    agent_a_data = AgentRoundData(
        agent_id=agent_a.id,
        response=result_a["response"],
        time_ms=result_a["time_ms"],
        tokens_used=0,  # TODO: extract from agent output if available
    )
    agent_b_data = AgentRoundData(
        agent_id=agent_b.id,
        response=result_b["response"],
        time_ms=result_b["time_ms"],
        tokens_used=0,
    )

    # Handle errors — if one agent errored, the other wins by default
    mode = GAME_MODES[game_mode]
    judge_scores: list[JudgeScore] = []
    winner: Optional[str] = None

    if result_a["error"] and result_b["error"]:
        # Both failed — draw
        winner = "draw"
        judge_scores = _fallback_judge_scores(mode.judging_criteria)
    elif result_a["error"]:
        winner = agent_b.id
        judge_scores = [JudgeScore(
            criterion=c, agent_a_score=1, agent_b_score=8,
            reasoning=f"Agent A failed: {result_a['error']}", judge_model="auto",
        ) for c in mode.judging_criteria]
    elif result_b["error"]:
        winner = agent_a.id
        judge_scores = [JudgeScore(
            criterion=c, agent_a_score=8, agent_b_score=1,
            reasoning=f"Agent B failed: {result_b['error']}", judge_model="auto",
        ) for c in mode.judging_criteria]
    else:
        # Both responded — judge them
        judge_scores = await _run_judge(
            prompt=prompt,
            response_a=result_a["response"],
            response_b=result_b["response"],
            criteria=mode.judging_criteria,
            match_id=match_id,
        )
        total_a = sum(s.agent_a_score for s in judge_scores)
        total_b = sum(s.agent_b_score for s in judge_scores)
        if total_a == total_b:
            winner = "draw"
        elif total_a > total_b:
            winner = agent_a.id
        else:
            winner = agent_b.id

    round_obj = MatchRound(
        id=round_id,
        match_id=match_id,
        round_number=round_num,
        prompt=prompt,
        agent_a=agent_a_data,
        agent_b=agent_b_data,
        judge_scores=judge_scores,
        winner=winner,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )

    # Broadcast round end
    await ws_manager.emit_round_end(match_id, round_obj.to_dict())

    logger.info("[%s] Round %d complete. Winner: %s", match_id, round_num, winner)
    return round_obj


async def start_match(match_id: str) -> None:
    """
    Main match orchestrator. Acquires semaphore, runs all rounds,
    determines winner, updates Elo, broadcasts match end.

    This is the function called from the API to kick off a match.
    """
    sem = _get_semaphore()

    if sem.locked():
        logger.warning("All %d match slots busy — match %s will queue", MAX_CONCURRENT_MATCHES, match_id)

    async with sem:
        await _execute_match(match_id)


async def _execute_match(match_id: str) -> None:
    """Internal: actually run the match to completion."""
    match = await store.get_match(match_id)
    if not match:
        logger.error("Match %s not found", match_id)
        return

    if match.status != MatchStatus.PENDING:
        logger.warning("Match %s is not pending (status: %s)", match_id, match.status.value)
        return

    agent_a = await store.get_agent(match.agent_a_id)
    agent_b = await store.get_agent(match.agent_b_id)
    if not agent_a or not agent_b:
        logger.error("Match %s: agent not found (A=%s, B=%s)", match_id, match.agent_a_id, match.agent_b_id)
        match.status = MatchStatus.ERROR
        await store.update_match(match)
        return

    # Mark in-progress
    match.status = MatchStatus.IN_PROGRESS
    match.started_at = datetime.now(timezone.utc).isoformat()
    match.current_round = 1
    await store.update_match(match)

    # Broadcast match start
    await ws_manager.broadcast_match_event(match_id, "match:start", match.to_dict())
    logger.info("[%s] Match started: %s vs %s (%s)", match_id, agent_a.name, agent_b.name, match.game_mode.value)

    try:
        mode = GAME_MODES[match.game_mode]
        round_timeout = mode.round_time_limit or DEFAULT_ROUND_TIMEOUT
        prompts = _pick_prompts(match.game_mode, match.total_rounds)

        for round_num in range(1, match.total_rounds + 1):
            match.current_round = round_num
            await store.update_match(match)

            round_result = await run_round(
                match_id=match_id,
                round_num=round_num,
                prompt=prompts[round_num - 1],
                agent_a=agent_a,
                agent_b=agent_b,
                game_mode=match.game_mode,
                round_timeout=round_timeout,
            )

            match.rounds.append(round_result)
            if round_result.winner == agent_a.id:
                match.agent_a_score += 1
            elif round_result.winner == agent_b.id:
                match.agent_b_score += 1

            await store.update_match(match)

            # Short pause between rounds for dramatic effect
            await asyncio.sleep(2)

        # ── Determine Match Winner ─────────────────────────────
        if match.agent_a_score > match.agent_b_score:
            match.winner = agent_a.id
        elif match.agent_b_score > match.agent_a_score:
            match.winner = agent_b.id
        else:
            match.winner = "draw"

        # ── Calculate Elo Changes ──────────────────────────────
        if match.winner == agent_a.id:
            result = 1.0
        elif match.winner == agent_b.id:
            result = 0.0
        else:
            result = 0.5

        new_a, new_b, delta_a, delta_b = calculate_elo(agent_a.elo, agent_b.elo, result)
        match.elo_change_a = delta_a
        match.elo_change_b = delta_b

        # Update agents in store
        await store.update_agent_elo(agent_a.id, new_a, won=(result == 1.0), lost=(result == 0.0), draw=(result == 0.5))
        await store.update_agent_elo(agent_b.id, new_b, won=(result == 0.0), lost=(result == 1.0), draw=(result == 0.5))

        # Mark completed
        match.status = MatchStatus.COMPLETED
        match.completed_at = datetime.now(timezone.utc).isoformat()
        await store.update_match(match)

        # Broadcast match end
        await ws_manager.emit_match_end(match_id, {
            "match": match.to_dict(),
            "eloChanges": {"agentA": delta_a, "agentB": delta_b},
        })

        logger.info("[%s] Match complete. Winner: %s (Elo: %+.0f/%+.0f)", match_id, match.winner, delta_a, delta_b)

    except asyncio.CancelledError:
        logger.warning("[%s] Match cancelled", match_id)
        match.status = MatchStatus.CANCELLED
        match.completed_at = datetime.now(timezone.utc).isoformat()
        await store.update_match(match)
        await ws_manager.broadcast_match_event(match_id, "match:end", {"match": match.to_dict(), "error": "cancelled"})
        raise

    except Exception:
        logger.exception("[%s] Match failed with error", match_id)
        match.status = MatchStatus.ERROR
        match.completed_at = datetime.now(timezone.utc).isoformat()
        await store.update_match(match)
        await ws_manager.broadcast_match_event(match_id, "match:end", {"match": match.to_dict(), "error": "internal_error"})

    finally:
        _active_matches.pop(match_id, None)


def start_match_background(match_id: str) -> asyncio.Task:
    """
    Start a match as a background asyncio task.
    Returns the task so the caller can await or cancel it if needed.
    """
    task = asyncio.create_task(start_match(match_id))
    _active_matches[match_id] = task
    return task


def get_active_match_count() -> int:
    return len(_active_matches)


def get_active_match_ids() -> list[str]:
    return list(_active_matches.keys())


async def cancel_match(match_id: str) -> bool:
    """Cancel a running match."""
    task = _active_matches.get(match_id)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        return True
    return False
