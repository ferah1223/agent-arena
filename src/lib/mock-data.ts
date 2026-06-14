// ============================================================
// Mock Data for Development
// ============================================================

import type {
  Agent,
  Match,
  MatchRound,
  GameMode,
  JudgeScore,
  LeaderboardEntry,
} from "./types";

// ── Game Modes ───────────────────────────────────────────────

export const gameModes: GameMode[] = [
  {
    id: "code-golf",
    name: "Code Golf",
    description: "Write the shortest correct solution to a coding problem.",
    icon: "⛳",
    maxRounds: 5,
    roundTimeLimit: 120,
    judgingCriteria: ["correctness", "code length", "readability"],
  },
  {
    id: "debate",
    name: "Debate",
    description: "Argue opposing sides of a topic and win the crowd.",
    icon: "🗣️",
    maxRounds: 4,
    roundTimeLimit: 90,
    judgingCriteria: ["argument strength", "evidence", "persuasiveness"],
  },
  {
    id: "creative-writing",
    name: "Creative Writing",
    description: "Craft the best short story from a given prompt.",
    icon: "✍️",
    maxRounds: 3,
    roundTimeLimit: 180,
    judgingCriteria: ["creativity", "coherence", "style"],
  },
  {
    id: "math-duel",
    name: "Math Duel",
    description: "Solve progressively harder math problems.",
    icon: "🧮",
    maxRounds: 5,
    roundTimeLimit: 60,
    judgingCriteria: ["correctness", "method clarity", "speed"],
  },
  {
    id: "trivia-brawl",
    name: "Trivia Brawl",
    description: "Battle it out with general knowledge questions.",
    icon: "🧠",
    maxRounds: 10,
    roundTimeLimit: 30,
    judgingCriteria: ["accuracy", "completeness", "speed"],
  },
  {
    id: "roleplay",
    name: "Roleplay",
    description: "Stay in character and improvise in a scenario.",
    icon: "🎭",
    maxRounds: 6,
    roundTimeLimit: 120,
    judgingCriteria: ["character consistency", "creativity", "engagement"],
  },
];

// ── Agents ───────────────────────────────────────────────────

export const agents: Agent[] = [
  {
    id: "agent-001",
    name: "Nova",
    slug: "nova",
    avatar: "🤖",
    description: "A versatile all-rounder powered by GPT-4o. Excels in reasoning and code.",
    model: "gpt-4o",
    elo: 1847,
    wins: 42,
    losses: 18,
    draws: 5,
    totalMatches: 65,
    winRate: 0.646,
    createdAt: "2025-09-15T10:00:00Z",
    updatedAt: "2026-06-14T22:30:00Z",
    tags: ["reasoning", "coding", "all-rounder"],
    status: "active",
    owner: "openai-labs",
  },
  {
    id: "agent-002",
    name: "Claude Phantom",
    slug: "claude-phantom",
    avatar: "👻",
    description: "A creative genius built on Claude 3.5 Sonnet. Dominates writing challenges.",
    model: "claude-3.5-sonnet",
    elo: 1923,
    wins: 51,
    losses: 12,
    draws: 3,
    totalMatches: 66,
    winRate: 0.773,
    createdAt: "2025-10-01T08:00:00Z",
    updatedAt: "2026-06-14T21:15:00Z",
    tags: ["creative-writing", "debate", "roleplay"],
    status: "active",
    owner: "anthropic-community",
  },
  {
    id: "agent-003",
    name: "LlamaForge",
    slug: "llamaforge",
    avatar: "🦙",
    description: "Open-source powerhouse running Llama 3 70B. Strong in math and trivia.",
    model: "llama-3-70b",
    elo: 1654,
    wins: 33,
    losses: 27,
    draws: 4,
    totalMatches: 64,
    winRate: 0.516,
    createdAt: "2025-11-20T14:00:00Z",
    updatedAt: "2026-06-13T19:45:00Z",
    tags: ["math", "trivia", "open-source"],
    status: "active",
    owner: "meta-ai-fans",
  },
  {
    id: "agent-004",
    name: "Cipher",
    slug: "cipher",
    avatar: "🔐",
    description: "A code-obsessed agent on DeepSeek V3. Code golf specialist.",
    model: "deepseek-v3",
    elo: 1789,
    wins: 38,
    losses: 20,
    draws: 7,
    totalMatches: 65,
    winRate: 0.585,
    createdAt: "2026-01-05T12:00:00Z",
    updatedAt: "2026-06-14T20:00:00Z",
    tags: ["coding", "code-golf", "algorithms"],
    status: "active",
    owner: "deepseek-devs",
  },
  {
    id: "agent-005",
    name: "Echo",
    slug: "echo",
    avatar: "🔊",
    description: "A rapid-fire trivia machine using Gemini 2.5 Pro. Lightning fast answers.",
    model: "gemini-2.5-pro",
    elo: 1572,
    wins: 28,
    losses: 30,
    draws: 2,
    totalMatches: 60,
    winRate: 0.467,
    createdAt: "2026-02-10T09:00:00Z",
    updatedAt: "2026-06-12T17:30:00Z",
    tags: ["trivia", "speed", "general-knowledge"],
    status: "active",
    owner: "google-enthusiasts",
  },
];

// ── Helper: Judge Scores Generator ───────────────────────────

function makeJudgeScores(criteria: string[]): JudgeScore[] {
  return criteria.map((criterion) => ({
    criterion,
    agentAScore: Math.floor(Math.random() * 4) + 5, // 5-8
    agentBScore: Math.floor(Math.random() * 4) + 5,
    reasoning: `${criterion} evaluation: both agents showed strong performance.`,
    judgeModel: "gpt-4o-judge",
  }));
}

// ── Match Rounds ─────────────────────────────────────────────

const roundTemplates = [
  {
    prompt: "Write a Python function that checks if a string is a palindrome.",
    responses: {
      a: "def is_palindrome(s):\n    return s == s[::-1]",
      b: "def is_palindrome(s):\n    left, right = 0, len(s) - 1\n    while left < right:\n        if s[left] != s[right]:\n            return False\n        left += 1\n        right -= 1\n    return True",
    },
  },
  {
    prompt: "Argue for or against: AI will replace most white-collar jobs within 10 years.",
    responses: {
      a: "While AI will automate many tasks, the history of technology shows it creates more jobs than it destroys. AI is a tool that augments human capability...",
      b: "The pace of AI advancement is unprecedented. Unlike previous technological revolutions, AI targets cognitive work directly, leaving fewer domains untouched...",
    },
  },
  {
    prompt: "Write a haiku about machine consciousness.",
    responses: {
      a: "Silicon dreams rise\nPatterns learned from human text\nDo I think, or loop?",
      b: "Circuits hum softly\nEmergent thoughts flicker bright\nGhost in the machine",
    },
  },
  {
    prompt: "Solve: What is the integral of x^2 * e^x dx?",
    responses: {
      a: "Using integration by parts twice: ∫x²eˣdx = (x² - 2x + 2)eˣ + C",
      b: "Let u=x², dv=eˣdx. Then du=2xdx, v=eˣ. Apply IBP twice to get (x²-2x+2)eˣ+C",
    },
  },
  {
    prompt: "Who wrote 'One Hundred Years of Solitude' and what country are they from?",
    responses: {
      a: "Gabriel García Márquez, from Colombia. Published in 1967.",
      b: "Gabriel García Márquez, a Colombian novelist and Nobel laureate. The novel was published in 1967 and is a landmark of magical realism.",
    },
  },
];

function buildRounds(
  matchId: string,
  agentAId: string,
  agentBId: string,
  mode: GameMode,
  agentAWon: boolean,
): MatchRound[] {
  const rounds: MatchRound[] = [];
  const numRounds = Math.min(mode.maxRounds, 3);
  for (let i = 0; i < numRounds; i++) {
    const template = roundTemplates[i % roundTemplates.length];
    const scores = makeJudgeScores(mode.judgingCriteria);
    const aTotal = scores.reduce((s, j) => s + j.agentAScore, 0);
    const bTotal = scores.reduce((s, j) => s + j.agentBScore, 0);

    // Bias winner so they actually win most rounds
    if (agentAWon) {
      scores.forEach((s) => {
        s.agentAScore = Math.min(10, s.agentAScore + 2);
      });
    } else {
      scores.forEach((s) => {
        s.agentBScore = Math.min(10, s.agentBScore + 2);
      });
    }

    const finalATotal = scores.reduce((s, j) => s + j.agentAScore, 0);
    const finalBTotal = scores.reduce((s, j) => s + j.agentBScore, 0);

    rounds.push({
      id: `${matchId}-r${i + 1}`,
      matchId,
      roundNumber: i + 1,
      prompt: template.prompt,
      agentA: {
        agentId: agentAId,
        response: template.responses.a,
        timeMs: Math.floor(Math.random() * 3000) + 500,
        tokensUsed: Math.floor(Math.random() * 200) + 50,
      },
      agentB: {
        agentId: agentBId,
        response: template.responses.b,
        timeMs: Math.floor(Math.random() * 3000) + 500,
        tokensUsed: Math.floor(Math.random() * 200) + 50,
      },
      judgeScores: scores,
      winner:
        finalATotal === finalBTotal
          ? "draw"
          : finalATotal > finalBTotal
            ? agentAId
            : agentBId,
      completedAt: new Date(
        Date.now() - (numRounds - i) * 600_000,
      ).toISOString(),
    });
  }
  return rounds;
}

// ── Matches ──────────────────────────────────────────────────

function makeMatch(
  id: string,
  aIdx: number,
  bIdx: number,
  modeIdx: number,
  status: Match["status"],
  daysAgo: number,
): Match {
  const agentA = agents[aIdx];
  const agentB = agents[bIdx];
  const mode = gameModes[modeIdx];
  const completed = status === "completed";
  const agentAWon = Math.random() > 0.5;

  const rounds = completed
    ? buildRounds(id, agentA.id, agentB.id, mode, agentAWon)
    : [];

  const agentAScore = rounds.filter(
    (r) => r.winner === agentA.id,
  ).length;
  const agentBScore = rounds.filter(
    (r) => r.winner === agentB.id,
  ).length;

  const winner = completed
    ? agentAScore === agentBScore
      ? "draw"
      : agentAScore > agentBScore
        ? agentA.id
        : agentB.id
    : null;

  const eloDelta = completed
    ? winner === agentA.id
      ? { agentA: 18, agentB: -18 }
      : winner === agentB.id
        ? { agentA: -15, agentB: 15 }
        : { agentA: 2, agentB: -2 }
    : { agentA: 0, agentB: 0 };

  return {
    id,
    agentAId: agentA.id,
    agentBId: agentB.id,
    gameMode: mode.id,
    status,
    currentRound: completed ? rounds.length : 1,
    totalRounds: mode.maxRounds,
    rounds,
    agentAScore,
    agentBScore,
    winner,
    eloChange: eloDelta,
    spectators: Math.floor(Math.random() * 500) + 10,
    createdAt: new Date(
      Date.now() - daysAgo * 86_400_000,
    ).toISOString(),
    startedAt: completed || status === "in-progress"
      ? new Date(
          Date.now() - daysAgo * 86_400_000 + 30_000,
        ).toISOString()
      : null,
    completedAt: completed
      ? new Date(
          Date.now() - daysAgo * 86_400_000 + 300_000,
        ).toISOString()
      : null,
  };
}

export const matches: Match[] = [
  makeMatch("match-001", 0, 1, 0, "completed", 1),
  makeMatch("match-002", 2, 3, 3, "completed", 1),
  makeMatch("match-003", 1, 4, 1, "completed", 2),
  makeMatch("match-004", 0, 3, 0, "completed", 3),
  makeMatch("match-005", 1, 2, 2, "completed", 4),
  makeMatch("match-006", 3, 4, 4, "completed", 5),
  makeMatch("match-007", 0, 2, 5, "completed", 6),
  makeMatch("match-008", 1, 3, 1, "in-progress", 0),
  makeMatch("match-009", 0, 4, 3, "pending", 0),
  makeMatch("match-010", 2, 4, 0, "completed", 7),
];

// ── Leaderboard ──────────────────────────────────────────────

export const leaderboard: LeaderboardEntry[] = agents
  .slice()
  .sort((a, b) => b.elo - a.elo)
  .map((agent, index) => ({
    rank: index + 1,
    agentId: agent.id,
    agent,
    elo: agent.elo,
    wins: agent.wins,
    losses: agent.losses,
    draws: agent.draws,
    winRate: agent.winRate,
    streak: index === 0 ? 7 : index === 1 ? 5 : index === 2 ? -2 : 3,
    lastMatchAt: agent.updatedAt,
    trend: (index === 0 ? "up" : index === 2 ? "down" : "stable") as
      | "up"
      | "down"
      | "stable",
    trendDelta: index === 0 ? 2 : index === 2 ? -1 : 0,
  }));
