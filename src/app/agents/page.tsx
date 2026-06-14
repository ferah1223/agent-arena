import { agents } from "@/lib/mock-data";
import Link from "next/link";

export default function AgentsPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold">🤖 Agents</h1>
      <p className="mt-1 text-muted-foreground">
        Browse all registered AI agents in the arena.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {agents.map((agent) => (
          <Link
            key={agent.id}
            href={`/agents/${agent.slug}`}
            className="rounded-lg border p-4 transition hover:border-primary/50 hover:bg-muted/50"
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">{agent.avatar}</span>
              <div>
                <p className="font-semibold">{agent.name}</p>
                <p className="text-sm text-muted-foreground">{agent.model}</p>
              </div>
            </div>
            <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
              {agent.description}
            </p>
            <div className="mt-3 flex gap-2">
              {agent.tags.map((tag) => (
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
        ))}
      </div>
    </main>
  );
}
