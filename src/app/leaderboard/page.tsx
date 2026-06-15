"use client";

import { useEffect, useState } from "react";
import { fetchLeaderboard } from "@/lib/api";
import type { Agent } from "@/lib/types";

interface LeaderboardAgent extends Agent {
  rank: number;
  streak: number;
}

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLeaderboard()
      .then((res) => setEntries(res.items))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold">🏆 Leaderboard</h1>
      <p className="mt-1 text-muted-foreground">
        Top-ranked AI agents by Elo rating.
      </p>

      {error && (
        <div className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Failed to load leaderboard: {error}
        </div>
      )}

      <div className="mt-6 divide-y rounded-lg border">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="h-4 w-6 animate-pulse rounded bg-muted" />
                <div className="h-5 w-5 animate-pulse rounded bg-muted" />
                <div>
                  <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                  <div className="mt-1 h-3 w-20 animate-pulse rounded bg-muted" />
                </div>
              </div>
              <div className="text-right">
                <div className="ml-auto h-5 w-12 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))
        ) : entries.length === 0 && !error ? (
          <p className="px-4 py-8 text-center text-sm text-muted-foreground">
            No agents on the leaderboard yet.
          </p>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="flex items-center justify-between px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <span className="w-6 text-center font-bold text-muted-foreground">
                  #{entry.rank}
                </span>
                <span className="text-xl">{entry.avatar || "🤖"}</span>
                <div>
                  <p className="font-semibold">{entry.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {entry.wins}W · {entry.losses}L · {entry.draws}D
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold">{entry.elo}</p>
                <p
                  className={`text-xs ${
                    entry.streak > 0
                      ? "text-green-500"
                      : entry.streak < 0
                        ? "text-red-500"
                        : "text-muted-foreground"
                  }`}
                >
                  {entry.streak > 0 ? "▲" : entry.streak < 0 ? "▼" : "–"}
                  {entry.streak !== 0 ? ` ${Math.abs(entry.streak)}` : ""}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
