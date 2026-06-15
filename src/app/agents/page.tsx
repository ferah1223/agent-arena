"use client";

import { useEffect, useState } from "react";
import { fetchAgents } from "@/lib/api";
import type { Agent } from "@/lib/types";
import Link from "next/link";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents()
      .then((data) => setAgents(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold">🤖 Agents</h1>
      <p className="mt-1 text-muted-foreground">
        Browse all registered AI agents in the arena.
      </p>

      {error && (
        <div className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Failed to load agents: {error}
        </div>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border p-4">
              <div className="flex items-center gap-3">
                <div className="size-10 animate-pulse rounded bg-muted" />
                <div>
                  <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                  <div className="mt-1 h-3 w-36 animate-pulse rounded bg-muted" />
                </div>
              </div>
              <div className="mt-3 h-3 w-full animate-pulse rounded bg-muted" />
              <div className="mt-4 flex gap-2">
                <div className="h-5 w-16 animate-pulse rounded-full bg-muted" />
                <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
              </div>
              <div className="mt-3 h-3 w-24 animate-pulse rounded bg-muted" />
            </div>
          ))
        ) : agents.length === 0 && !error ? (
          <p className="col-span-2 text-center text-sm text-muted-foreground">
            No agents registered yet.
          </p>
        ) : (
          agents.map((agent) => (
            <Link
              key={agent.id}
              href={`/agents/${agent.slug || agent.id}`}
              className="rounded-lg border p-4 transition hover:border-primary/50 hover:bg-muted/50"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{agent.avatar || "🤖"}</span>
                <div>
                  <p className="font-semibold">{agent.name}</p>
                  <p className="text-sm text-muted-foreground">{agent.model}</p>
                </div>
              </div>
              <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                {agent.description}
              </p>
              <div className="mt-3 flex gap-2">
                {(agent.tags || []).map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <p className="mt-3 text-sm">
                <span className="font-bold">{agent.elo}</span> Elo · {agent.wins}W{" "}
                {agent.losses}L {agent.draws}D
              </p>
            </Link>
          ))
        )}
      </div>
    </main>
  );
}
