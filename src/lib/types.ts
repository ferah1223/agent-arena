// ============================================================
// Agent Arena – Core Type Definitions
// ============================================================

/** Unique identifier type aliases for clarity */
export type AgentId = string;
export type MatchId = string;
export type RoundId = string;

// ── Agent ────────────────────────────────────────────────────

export interface Agent {
  id: AgentId;
  name: string;
  slug: string;
  avatar: string; // URL or emoji
  description: string;
  model: string; // e.g. "gpt-4o", "claude-3.5-sonnet", "llama-3-70b"
  elo: number;
  wins: number;
  losses: number;
  draws: number;
  totalMatches: number;
  winRate: number; // 0-1
  createdAt: string; // ISO 8601
  updatedAt: string;
  tags: string[]; // e.g. ["coding", "reasoning", "creative"]
  status: "active" | "idle" | "retired";
  owner: string; // username or org
}

// ── Game Mode ────────────────────────────────────────────────

export type GameModeId =
  | "code-golf"
  | "debate"
  | "creative-writing"
  | "math-duel"
  | "trivia-brawl"
  | "roleplay";

export interface GameMode {
  id: GameModeId;
  name: string;
  description: string;
  icon: string; // emoji
  maxRounds: number;
  roundTimeLimit: number; // seconds
  judgingCriteria: string[];
}

// ── Match & Rounds ───────────────────────────────────────────

export type MatchStatus =
  | "pending"
  | "in-progress"
  | "completed"
  | "cancelled"
  | "error";

export interface MatchRound {
  id: RoundId;
  matchId: MatchId;
  roundNumber: number;
  prompt: string;
  agentA: {
    agentId: AgentId;
    response: string;
    timeMs: number; // response time in ms
    tokensUsed: number;
  };
  agentB: {
    agentId: AgentId;
    response: string;
    timeMs: number;
    tokensUsed: number;
  };
  judgeScores: JudgeScore[];
  winner: AgentId | "draw" | null;
  completedAt: string | null;
}

export interface Match {
  id: MatchId;
  agentAId: AgentId;
  agentBId: AgentId;
  gameMode: GameModeId;
  status: MatchStatus;
  currentRound: number;
  totalRounds: number;
  rounds: MatchRound[];
  agentAScore: number; // cumulative
  agentBScore: number;
  winner: AgentId | "draw" | null;
  eloChange: {
    agentA: number; // delta (can be negative)
    agentB: number;
  };
  spectators: number;
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
}

// ── Judging ──────────────────────────────────────────────────

export interface JudgeScore {
  criterion: string; // e.g. "accuracy", "creativity", "clarity"
  agentAScore: number; // 1-10
  agentBScore: number; // 1-10
  reasoning: string;
  judgeModel: string; // model used as judge
}

// ── Leaderboard ──────────────────────────────────────────────

export interface LeaderboardEntry {
  rank: number;
  agentId: AgentId;
  agent: Agent;
  elo: number;
  wins: number;
  losses: number;
  draws: number;
  winRate: number;
  streak: number; // positive = win streak, negative = loss streak
  lastMatchAt: string;
  trend: "up" | "down" | "stable";
  trendDelta: number; // rank change since last period
}

// ── WebSocket Messages ───────────────────────────────────────

export type WSEventType =
  | "match:start"
  | "match:end"
  | "round:start"
  | "round:end"
  | "round:response"
  | "round:judging"
  | "spectator:join"
  | "spectator:leave"
  | "chat:message"
  | "leaderboard:update";

export interface WebSocketMessage {
  event: WSEventType;
  payload: unknown;
  timestamp: string;
  matchId?: MatchId;
}

export interface WSMatchStartPayload {
  match: Match;
}

export interface WSMatchEndPayload {
  match: Match;
  eloChanges: Match["eloChange"];
}

export interface WSRoundResponsePayload {
  matchId: MatchId;
  round: MatchRound;
  agent: "A" | "B";
  partialResponse: string; // for streaming
  done: boolean;
}

export interface WSRoundJudgingPayload {
  matchId: MatchId;
  round: MatchRound;
  judgeScores: JudgeScore[];
}

export interface WSChatMessagePayload {
  matchId: MatchId;
  username: string;
  avatar: string;
  message: string;
  timestamp: string;
}

// ── Utility types ────────────────────────────────────────────

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
