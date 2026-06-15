"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import { fetchMatch, startMatch } from "@/lib/api";
import { connectToMatch } from "@/lib/ws";
import type { Match } from "@/lib/types";

export default function MatchPage() {
  const params = useParams();
  const matchId = params.id as string;

  const [match, setMatch] = useState<Match | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [starting, setStarting] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);

  // Fetch match on mount
  useEffect(() => {
    if (!matchId) return;

    let cancelled = false;
    fetchMatch(matchId)
      .then((data) => {
        if (!cancelled) setMatch(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [matchId]);

  // Connect WebSocket for live updates
  useEffect(() => {
    if (!matchId) return;

    const cleanup = connectToMatch(
      matchId,
      (data) => {
        const msgType = data.type as string;

        if (msgType === "connected") {
          setWsConnected(true);
          return;
        }

        // Handle match update events
        if (msgType === "match:start" || msgType === "match:update" || msgType === "match:end") {
          const updatedMatch = data.data as Match;
          if (updatedMatch) {
            setMatch(updatedMatch);
          }
        }

        // Handle round events — refetch the full match
        if (
          msgType === "round:start" ||
          msgType === "round:end" ||
          msgType === "round:response" ||
          msgType === "round:judging"
        ) {
          fetchMatch(matchId)
            .then((data) => setMatch(data))
            .catch(() => {});
        }
      },
      () => setWsConnected(true),
      () => setWsConnected(false),
    );

    cleanupRef.current = cleanup;
    return () => cleanup();
  }, [matchId]);

  const handleStart = useCallback(async () => {
    if (!matchId) return;
    setStarting(true);
    try {
      await startMatch(matchId);
      // The match will update via WebSocket, but also refetch after a delay
      setTimeout(() => {
        fetchMatch(matchId)
          .then((data) => setMatch(data))
          .catch(() => {});
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start match");
    } finally {
      setStarting(false);
    }
  }, [matchId]);

  if (loading) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-12">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="mt-2 h-4 w-48 animate-pulse rounded bg-muted" />
        <div className="mt-8 h-40 animate-pulse rounded-lg bg-muted" />
      </main>
    );
  }

  if (error && !match) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-12">
        <h1 className="text-2xl font-bold">Match not found</h1>
        <p className="mt-2 text-muted-foreground">
          Could not load match &quot;{matchId}&quot;: {error}
        </p>
      </main>
    );
  }

  if (!match) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-12">
        <h1 className="text-2xl font-bold">Match not found</h1>
        <p className="mt-2 text-muted-foreground">
          No match with ID &quot;{matchId}&quot; exists.
        </p>
      </main>
    );
  }

  const statusColors: Record<string, string> = {
    "in-progress": "text-emerald-400",
    pending: "text-amber-400",
    completed: "text-blue-400",
    cancelled: "text-red-400",
    error: "text-red-400",
  };

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {match.agentAId} vs {match.agentBId}
          </h1>
          <p className="mt-1 text-muted-foreground">
            {match.gameMode} ·{" "}
            <span className={statusColors[match.status] || ""}>
              {match.status}
            </span>{" "}
            · {match.spectators} spectators
            {wsConnected && (
              <span className="ml-2 inline-flex items-center gap-1">
                <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-400 text-xs">live</span>
              </span>
            )}
          </p>
        </div>

        {match.status === "pending" && (
          <button
            onClick={handleStart}
            disabled={starting}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:opacity-50"
          >
            {starting ? "Starting..." : "Start Match"}
          </button>
        )}
      </div>

      {/* Scores */}
      <section className="mt-8 rounded-lg border bg-white/[0.02] p-6">
        <div className="flex items-center justify-center gap-8">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">{match.agentAId}</p>
            <p className="mt-1 text-4xl font-bold">{match.agentAScore}</p>
          </div>
          <span className="text-2xl font-bold text-muted-foreground">–</span>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">{match.agentBId}</p>
            <p className="mt-1 text-4xl font-bold">{match.agentBScore}</p>
          </div>
        </div>

        {match.winner && (
          <p className="mt-4 text-center text-lg font-semibold">
            {match.winner === "draw" ? (
              "Draw"
            ) : (
              <>
                🏆 Winner:{" "}
                <span className="text-amber-400">{match.winner}</span>
              </>
            )}
          </p>
        )}
      </section>

      {/* Rounds */}
      <section className="mt-8">
        <h2 className="text-xl font-semibold">
          Rounds ({match.rounds?.length ?? 0})
        </h2>

        {match.rounds && match.rounds.length > 0 ? (
          <div className="mt-4 space-y-4">
            {match.rounds.map((round) => (
              <div
                key={round.id}
                className="rounded-lg border bg-white/[0.02] p-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">
                    Round {round.roundNumber}
                  </h3>
                  {round.winner && (
                    <span className="text-sm text-muted-foreground">
                      Winner:{" "}
                      {round.winner === "draw"
                        ? "Draw"
                        : round.winner}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {round.prompt}
                </p>

                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div className="rounded border p-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      {round.agentA.agentId}
                    </p>
                    <p className="mt-1 whitespace-pre-wrap text-sm">
                      {round.agentA.response}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {round.agentA.timeMs}ms · {round.agentA.tokensUsed} tokens
                    </p>
                  </div>
                  <div className="rounded border p-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      {round.agentB.agentId}
                    </p>
                    <p className="mt-1 whitespace-pre-wrap text-sm">
                      {round.agentB.response}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {round.agentB.timeMs}ms · {round.agentB.tokensUsed} tokens
                    </p>
                  </div>
                </div>

                {round.judgeScores && round.judgeScores.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      Judge Scores
                    </p>
                    <div className="mt-1 space-y-1">
                      {round.judgeScores.map((score, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between text-xs"
                        >
                          <span>{score.criterion}</span>
                          <span>
                            {score.agentAScore} – {score.agentBScore}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-muted-foreground">
            {match.status === "pending"
              ? "Match hasn't started yet."
              : match.status === "in-progress"
                ? "Waiting for round data..."
                : "No rounds recorded."}
          </p>
        )}
      </section>

      {/* Error banner */}
      {error && (
        <div className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}
    </main>
  );
}
