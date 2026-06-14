from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Agent models ---

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    model: str = Field(..., min_length=1, max_length=128)
    owner: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=2048)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    model: Optional[str] = Field(None, min_length=1, max_length=128)
    owner: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=2048)


class AgentResponse(BaseModel):
    id: int
    name: str
    model: str
    owner: str
    description: str
    api_key: Optional[str] = None
    elo: int
    wins: int
    losses: int
    streak: int
    created_at: str


class AgentListResponse(BaseModel):
    items: List[AgentResponse]
    total: int
    page: int
    page_size: int


# --- Match models ---

class MatchCreate(BaseModel):
    agent_a_id: int
    agent_b_id: int
    game_mode: str = Field(..., min_length=1, max_length=64)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard|extreme)$")


class RoundResponse(BaseModel):
    id: int
    match_id: int
    round_num: int
    agent_id: int
    input_prompt: str
    output_response: str
    score: float
    timestamp: str


class MatchResponse(BaseModel):
    id: int
    agent_a_id: int
    agent_b_id: int
    game_mode: str
    difficulty: str
    status: str
    winner_id: Optional[int]
    agent_a_score: float
    agent_b_score: float
    created_at: str
    completed_at: Optional[str] = None


class MatchDetailResponse(MatchResponse):
    rounds: List[RoundResponse] = []


class MatchListResponse(BaseModel):
    items: List[MatchResponse]
    total: int
    page: int
    page_size: int


# --- Challenge models ---

class ChallengeCreate(BaseModel):
    mode: str = Field(..., min_length=1, max_length=64)
    difficulty: str = Field(..., pattern="^(easy|medium|hard|extreme)$")
    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=4096)
    content_json: str = Field(default="{}")
    time_limit: int = Field(default=60, ge=1, le=3600)


class ChallengeResponse(BaseModel):
    id: int
    mode: str
    difficulty: str
    title: str
    description: str
    content_json: str
    time_limit: int
    created_at: str


# --- Leaderboard ---

class LeaderboardEntry(BaseModel):
    rank: int
    id: int
    name: str
    model: str
    owner: str
    elo: int
    wins: int
    losses: int
    streak: int


class LeaderboardResponse(BaseModel):
    items: List[LeaderboardEntry]
    total: int
