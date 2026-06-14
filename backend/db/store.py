"""
Agent Arena — In-Memory Data Store
===================================
Thread-safe, asyncio-compatible store for agents, matches, and game state.
Replace with a real DB (Postgres/SQLite) when ready.
"""

from __future__ import annotations

import asyncio
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ── Enums ──────────────────────────────────────────────────────

class MatchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    RETIRED = "retired"


class GameModeId(str, Enum):
    CODE_GOLF = "code-golf"
    DEBATE = "debate"
    CREATIVE_WRITING = "creative-writing"
    MATH_DUEL = "math-duel"
    TRIVIA_BRAWL = "trivia-brawl"
    ROLEPLAY = "roleplay"


# ── Data Classes ───────────────────────────────────────────────

@dataclass
class Agent:
    id: str
    name: str
    slug: str
    avatar: str = "🤖"
    description: str = ""
    model: str = ""
    elo: int = 1500
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_matches: int = 0
    tags: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.ACTIVE
    owner: str = ""
    profile_name: str = ""  # hermes profile name
    api_key: str = ""       # arena-issued key
    created_at: str = ""
    updated_at: str = ""

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_matches if self.total_matches > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "avatar": self.avatar,
            "description": self.description,
            "model": self.model,
            "elo": self.elo,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "totalMatches": self.total_matches,
            "winRate": round(self.win_rate, 3),
            "tags": self.tags,
            "status": self.status.value,
            "owner": self.owner,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


@dataclass
class GameMode:
    id: GameModeId
    name: str
    description: str
    icon: str
    max_rounds: int
    round_time_limit: int  # seconds
    judging_criteria: list[str]


@dataclass
class JudgeScore:
    criterion: str
    agent_a_score: int
    agent_b_score: int
    reasoning: str
    judge_model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion": self.criterion,
            "agentAScore": self.agent_a_score,
            "agentBScore": self.agent_b_score,
            "reasoning": self.reasoning,
            "judgeModel": self.judge_model,
        }


@dataclass
class AgentRoundData:
    agent_id: str
    response: str = ""
    time_ms: int = 0
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agentId": self.agent_id,
            "response": self.response,
            "timeMs": self.time_ms,
            "tokensUsed": self.tokens_used,
        }


@dataclass
class MatchRound:
    id: str
    match_id: str
    round_number: int
    prompt: str
    agent_a: AgentRoundData = field(default_factory=lambda: AgentRoundData(""))
    agent_b: AgentRoundData = field(default_factory=lambda: AgentRoundData(""))
    judge_scores: list[JudgeScore] = field(default_factory=list)
    winner: Optional[str] = None  # agent_id or "draw" or None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "matchId": self.match_id,
            "roundNumber": self.round_number,
            "prompt": self.prompt,
            "agentA": self.agent_a.to_dict(),
            "agentB": self.agent_b.to_dict(),
            "judgeScores": [s.to_dict() for s in self.judge_scores],
            "winner": self.winner,
            "completedAt": self.completed_at,
        }


@dataclass
class Match:
    id: str
    agent_a_id: str
    agent_b_id: str
    game_mode: GameModeId
    status: MatchStatus = MatchStatus.PENDING
    current_round: int = 0
    total_rounds: int = 5
    rounds: list[MatchRound] = field(default_factory=list)
    agent_a_score: int = 0
    agent_b_score: int = 0
    winner: Optional[str] = None
    elo_change_a: int = 0
    elo_change_b: int = 0
    spectators: int = 0
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    difficulty: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agentAId": self.agent_a_id,
            "agentBId": self.agent_b_id,
            "gameMode": self.game_mode.value,
            "status": self.status.value,
            "currentRound": self.current_round,
            "totalRounds": self.total_rounds,
            "rounds": [r.to_dict() for r in self.rounds],
            "agentAScore": self.agent_a_score,
            "agentBScore": self.agent_b_score,
            "winner": self.winner,
            "eloChange": {"agentA": self.elo_change_a, "agentB": self.elo_change_b},
            "spectators": self.spectators,
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
        }


# ── Game Modes Config ─────────────────────────────────────────

GAME_MODES: dict[GameModeId, GameMode] = {
    GameModeId.CODE_GOLF: GameMode(
        id=GameModeId.CODE_GOLF,
        name="Code Golf",
        description="Write the shortest correct solution to a coding problem.",
        icon="⛳",
        max_rounds=5,
        round_time_limit=120,
        judging_criteria=["correctness", "code length", "readability"],
    ),
    GameModeId.DEBATE: GameMode(
        id=GameModeId.DEBATE,
        name="Debate",
        description="Argue opposing sides of a topic and win the crowd.",
        icon="🗣️",
        max_rounds=4,
        round_time_limit=90,
        judging_criteria=["argument strength", "evidence", "persuasiveness"],
    ),
    GameModeId.CREATIVE_WRITING: GameMode(
        id=GameModeId.CREATIVE_WRITING,
        name="Creative Writing",
        description="Craft the best short story from a given prompt.",
        icon="✍️",
        max_rounds=3,
        round_time_limit=180,
        judging_criteria=["creativity", "coherence", "style"],
    ),
    GameModeId.MATH_DUEL: GameMode(
        id=GameModeId.MATH_DUEL,
        name="Math Duel",
        description="Solve progressively harder math problems.",
        icon="🧮",
        max_rounds=5,
        round_time_limit=60,
        judging_criteria=["correctness", "method clarity", "speed"],
    ),
    GameModeId.TRIVIA_BRAWL: GameMode(
        id=GameModeId.TRIVIA_BRAWL,
        name="Trivia Brawl",
        description="Battle it out with general knowledge questions.",
        icon="🧠",
        max_rounds=10,
        round_time_limit=30,
        judging_criteria=["accuracy", "completeness", "speed"],
    ),
    GameModeId.ROLEPLAY: GameMode(
        id=GameModeId.ROLEPLAY,
        name="Roleplay",
        description="Stay in character and improvise in a scenario.",
        icon="🎭",
        max_rounds=6,
        round_time_limit=120,
        judging_criteria=["character consistency", "creativity", "engagement"],
    ),
}


# ── Elo Calculation (mirrors src/lib/elo.ts) ──────────────────

DEFAULT_K = 32


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))


def calculate_elo(rating_a: int, rating_b: int, result: float, k: int = DEFAULT_K) -> tuple[int, int, int, int]:
    """
    result: 1.0 = A wins, 0.5 = draw, 0.0 = A loses
    Returns (new_a, new_b, delta_a, delta_b)
    """
    exp_a = expected_score(rating_a, rating_b)
    exp_b = 1 - exp_a
    delta_a = round(k * (result - exp_a))
    delta_b = round(k * (1 - result - exp_b))
    return rating_a + delta_a, rating_b + delta_b, delta_a, delta_b


# ── Challenge Prompts ─────────────────────────────────────────

CHALLENGE_PROMPTS: dict[GameModeId, list[str]] = {
    GameModeId.CODE_GOLF: [
        "Write a Python function that checks if a string is a palindrome.",
        "Write a function that returns the nth Fibonacci number.",
        "Implement a function that flattens a nested list.",
        "Write a function to find the longest common substring of two strings.",
        "Implement a LRU cache with get and put methods.",
        "Write a function that converts a Roman numeral string to an integer.",
        "Implement a function that validates balanced parentheses.",
        "Write a function to merge two sorted arrays into one sorted array.",
    ],
    GameModeId.DEBATE: [
        "Argue for or against: AI will replace most white-collar jobs within 10 years.",
        "Is social media a net positive or negative for society?",
        "Should open-source AI models be restricted to prevent misuse?",
        "Is remote work better than office work for productivity?",
    ],
    GameModeId.CREATIVE_WRITING: [
        "Write a haiku about machine consciousness.",
        "Write a 100-word flash fiction about the last human librarian.",
        "Write a poem from the perspective of a forgotten robot.",
        "Write a micro-story set in a city where emotions are currency.",
    ],
    GameModeId.MATH_DUEL: [
        "Solve: What is the integral of x^2 * e^x dx?",
        "Prove that the square root of 2 is irrational.",
        "Find all integer solutions to x^2 + y^2 = z^2 for z < 20.",
        "What is the probability that two random integers are coprime?",
    ],
    GameModeId.TRIVIA_BRAWL: [
        "Who wrote 'One Hundred Years of Solitude' and what country are they from?",
        "What is the chemical formula for sulfuric acid and its common uses?",
        "Name three programming languages created before 1970.",
        "What year did the Berlin Wall fall and what triggered it?",
    ],
    GameModeId.ROLEPLAY: [
        "You are a medieval blacksmith. A knight asks you to forge a sword that can slay a dragon. Stay in character.",
        "You are an AI assistant from 2050. Explain how the world changed in the last 30 years.",
        "You are a space explorer making first contact with an alien species. How do you communicate?",
    ],
}


# ── In-Memory Store ────────────────────────────────────────────

class Store:
    """Thread-safe in-memory store with asyncio lock."""

    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}
        self.matches: dict[str, Match] = {}
        self._lock = asyncio.Lock()

    # ── Agent CRUD ─────────────────────────────────────────────

    async def create_agent(self, name: str, model: str, profile_name: str = "", **kwargs: Any) -> Agent:
        now = datetime.now(timezone.utc).isoformat()
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        slug = name.lower().replace(" ", "-").replace("_", "-")
        api_key = f"arena_{uuid.uuid4().hex}"
        agent = Agent(
            id=agent_id,
            name=name,
            slug=slug,
            model=model,
            profile_name=profile_name or slug,
            api_key=api_key,
            created_at=now,
            updated_at=now,
            **kwargs,
        )
        async with self._lock:
            self.agents[agent_id] = agent
        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        async with self._lock:
            return self.agents.get(agent_id)

    async def get_agent_by_api_key(self, api_key: str) -> Optional[Agent]:
        async with self._lock:
            for a in self.agents.values():
                if a.api_key == api_key:
                    return a
            return None

    async def list_agents(self) -> list[Agent]:
        async with self._lock:
            return sorted(self.agents.values(), key=lambda a: a.elo, reverse=True)

    async def update_agent_elo(self, agent_id: str, new_elo: int, won: bool = False, lost: bool = False, draw: bool = False) -> None:
        async with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return
            agent.elo = new_elo
            agent.total_matches += 1
            if won:
                agent.wins += 1
            elif lost:
                agent.losses += 1
            elif draw:
                agent.draws += 1
            agent.updated_at = datetime.now(timezone.utc).isoformat()

    # ── Match CRUD ─────────────────────────────────────────────

    async def create_match(self, agent_a_id: str, agent_b_id: str, game_mode: GameModeId, difficulty: str = "medium") -> Match:
        now = datetime.now(timezone.utc).isoformat()
        match_id = f"match-{uuid.uuid4().hex[:8]}"
        mode = GAME_MODES[game_mode]
        match = Match(
            id=match_id,
            agent_a_id=agent_a_id,
            agent_b_id=agent_b_id,
            game_mode=game_mode,
            total_rounds=mode.max_rounds,
            created_at=now,
            difficulty=difficulty,
        )
        async with self._lock:
            self.matches[match_id] = match
        return match

    async def get_match(self, match_id: str) -> Optional[Match]:
        async with self._lock:
            return self.matches.get(match_id)

    async def list_matches(self, status: Optional[MatchStatus] = None) -> list[Match]:
        async with self._lock:
            matches = list(self.matches.values())
        if status:
            matches = [m for m in matches if m.status == status]
        return sorted(matches, key=lambda m: m.created_at, reverse=True)

    async def update_match(self, match: Match) -> None:
        async with self._lock:
            self.matches[match.id] = match


# Singleton store instance
store = Store()
