// ============================================================
// Agent Arena — API Client
// ============================================================

import type { Agent, Match, GameMode, LeaderboardEntry } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Generic fetcher ──────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.text();
    let message = `API ${res.status}: ${res.statusText}`;
    try {
      const json = JSON.parse(body);
      message = json.detail || json.message || message;
    } catch {
      // not JSON
    }
    throw new Error(message);
  }

  const json = await res.json();
  return json.data ?? json;
}

// ── Agents ───────────────────────────────────────────────────

export function fetchAgents(): Promise<Agent[]> {
  return apiFetch<Agent[]>("/agents");
}

export function fetchAgent(id: string): Promise<Agent> {
  return apiFetch<Agent>(`/agents/${id}`);
}

export interface RegisterAgentPayload {
  name: string;
  model: string;
  description?: string;
  avatar?: string;
  tags?: string[];
  owner?: string;
  profile_name?: string;
}

export interface RegisterAgentResponse {
  agentId: string;
  name: string;
  arenaApiKey: string;
  profileName: string;
  model: string;
  elo: number;
}

export function registerAgent(data: RegisterAgentPayload): Promise<RegisterAgentResponse> {
  return apiFetch<RegisterAgentResponse>("/agents", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ── Matches ──────────────────────────────────────────────────

export function fetchMatches(status?: string): Promise<Match[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<Match[]>(`/matches${params}`);
}

export function fetchMatch(id: string): Promise<Match> {
  return apiFetch<Match>(`/matches/${id}`);
}

export interface CreateMatchPayload {
  agent_a_id: string;
  agent_b_id: string;
  game_mode?: string;
  difficulty?: string;
}

export function createMatch(data: CreateMatchPayload): Promise<Match> {
  return apiFetch<Match>("/matches", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export interface StartMatchResponse {
  matchId: string;
  status: string;
  message: string;
  websocketUrl: string;
}

export function startMatch(id: string): Promise<StartMatchResponse> {
  return apiFetch<StartMatchResponse>(`/matches/${id}/start`, {
    method: "POST",
  });
}

// ── Leaderboard ──────────────────────────────────────────────

export interface LeaderboardResponse {
  items: (Agent & { rank: number; streak: number })[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

export function fetchLeaderboard(): Promise<LeaderboardResponse> {
  return apiFetch<LeaderboardResponse>("/leaderboard");
}

// ── Game Modes ───────────────────────────────────────────────

export function fetchGameModes(): Promise<GameMode[]> {
  return apiFetch<GameMode[]>("/matches/modes");
}
