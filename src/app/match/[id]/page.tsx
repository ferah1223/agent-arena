import { matches, agents } from "@/lib/mock-data";

export default function MatchPage({ params }: { params: { id: string } }) {
  const match = matches.find((m) => m.id === params.id);

  if (!match) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-12">
        <h1 className="text-2xl font-bold">Match not found</h1>
        <p className="mt-2 text-muted-foreground">
          No match with ID &quot;{params.id}&quot; exists.
        </p>
      </main>
    );
  }

  const agentA = agents.find((a) => a.id === match.agentAId);
  const agentB = agents.find((a) => a.id === match.agentBId);

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold">
        {agentA?.name ?? match.agentAId} vs {agentB?.name ?? match.agentBId}
      </h1>
      <p className="mt-1 text-muted-foreground">
        {match.gameMode} · {match.status} · {match.spectators} spectators
      </p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Rounds ({match.rounds.length})</h2>
        <p className="mt-2 text-muted-foreground">
          Score: {match.agentAScore} – {match.agentBScore}
        </p>
        {/* Full round detail to be implemented */}
      </section>
    </main>
  );
}
