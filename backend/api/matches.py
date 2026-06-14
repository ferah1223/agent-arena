"""
Agent Arena — Matches API
===========================
REST endpoints for match management.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.match_engine import (
    cancel_match,
    get_active_match_count,
    get_active_match_ids,
    start_match_background,
)
from db.store import (
    GAME_MODES,
    GameModeId,
    MatchStatus,
    store,
)

logger = logging.getLogger("arena.api.matches")

router = APIRouter(prefix="/matches", tags=["matches"])


# ── Request/Response Models ────────────────────────────────────

class CreateMatchRequest(BaseModel):
    agent_a_id: str
    agent_b_id: str
    game_mode: str = "code-golf"
    difficulty: str = "medium"


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/modes")
async def list_game_modes() -> dict[str, Any]:
    """List available game modes."""
    modes = []
    for mode in GAME_MODES.values():
        modes.append({
            "id": mode.id.value,
            "name": mode.name,
            "description": mode.description,
            "icon": mode.icon,
            "maxRounds": mode.max_rounds,
            "roundTimeLimit": mode.round_time_limit,
            "judgingCriteria": mode.judging_criteria,
        })
    return {"data": modes, "success": True}


@router.get("/active")
async def list_active_matches() -> dict[str, Any]:
    """List currently running matches."""
    active_ids = get_active_match_ids()
    active_matches = []
    for mid in active_ids:
        m = await store.get_match(mid)
        if m:
            active_matches.append(m.to_dict())
    return {
        "data": active_matches,
        "activeCount": get_active_match_count(),
        "maxConcurrent": 5,
    }


@router.get("")
async def list_matches(status: Optional[str] = None) -> dict[str, Any]:
    """List all matches, optionally filtered by status."""
    match_status = None
    if status:
        try:
            match_status = MatchStatus(status)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}. Use: pending, in-progress, completed, cancelled, error")

    matches = await store.list_matches(status=match_status)
    return {
        "data": [m.to_dict() for m in matches],
        "success": True,
        "total": len(matches),
    }


@router.post("")
async def create_match(req: CreateMatchRequest) -> dict[str, Any]:
    """Create a new match (does not start it automatically)."""
    # Validate agents exist
    agent_a = await store.get_agent(req.agent_a_id)
    agent_b = await store.get_agent(req.agent_b_id)
    if not agent_a:
        raise HTTPException(404, f"Agent {req.agent_a_id} not found")
    if not agent_b:
        raise HTTPException(404, f"Agent {req.agent_b_id} not found")
    if req.agent_a_id == req.agent_b_id:
        raise HTTPException(400, "Cannot match an agent against itself")

    # Validate game mode
    try:
        game_mode = GameModeId(req.game_mode)
    except ValueError:
        valid = [m.value for m in GameModeId]
        raise HTTPException(400, f"Invalid game mode: {req.game_mode}. Valid: {valid}")

    match = await store.create_match(
        agent_a_id=req.agent_a_id,
        agent_b_id=req.agent_b_id,
        game_mode=game_mode,
        difficulty=req.difficulty,
    )
    logger.info("Created match %s: %s vs %s (%s)", match.id, agent_a.name, agent_b.name, game_mode.value)

    return {
        "data": match.to_dict(),
        "success": True,
    }


@router.get("/{match_id}")
async def get_match(match_id: str) -> dict[str, Any]:
    """Get match details by ID."""
    match = await store.get_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")
    return {
        "data": match.to_dict(),
        "success": True,
    }


@router.post("/{match_id}/start")
async def start_match(match_id: str) -> dict[str, Any]:
    """
    Start a pending match. Spawns agent processes and begins rounds.
    The match runs as a background task — use WebSocket to watch live.
    """
    match = await store.get_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")

    if match.status != MatchStatus.PENDING:
        raise HTTPException(
            409,
            f"Match {match_id} is already {match.status.value}. "
            f"Only pending matches can be started."
        )

    # Check concurrent limit
    if get_active_match_count() >= 5:
        raise HTTPException(
            503,
            f"All {5} match slots are busy. Active: {get_active_match_ids()}. "
            f"Try again shortly."
        )

    # Launch as background task
    task = start_match_background(match_id)
    logger.info("Match %s start requested (task=%s)", match_id, task.get_name())

    return {
        "data": {
            "matchId": match_id,
            "status": "starting",
            "message": "Match is starting. Connect via WebSocket to watch live.",
            "websocketUrl": f"/ws/match/{match_id}",
        },
        "success": True,
    }


@router.post("/{match_id}/join")
async def join_match(match_id: str) -> dict[str, Any]:
    """
    Join as a viewer. Returns the WebSocket URL for live updates.
    Increments spectator count.
    """
    match = await store.get_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")

    # Increment spectator count
    match.spectators += 1
    await store.update_match(match)

    return {
        "data": {
            "matchId": match_id,
            "websocketUrl": f"/ws/match/{match_id}",
            "viewers": match.spectators,
            "status": match.status.value,
        },
        "success": True,
    }


@router.post("/{match_id}/cancel")
async def cancel_match_endpoint(match_id: str) -> dict[str, Any]:
    """Cancel a running match."""
    match = await store.get_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")

    if match.status not in (MatchStatus.PENDING, MatchStatus.IN_PROGRESS):
        raise HTTPException(409, f"Match {match_id} is already {match.status.value}")

    cancelled = await cancel_match(match_id)
    return {
        "data": {
            "matchId": match_id,
            "cancelled": cancelled,
            "status": "cancelled" if cancelled else match.status.value,
        },
        "success": True,
    }
