import { leaderboard } from "@/lib/mock-data";

export default function LeaderboardPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold">🏆 Leaderboard</h1>
      <p className="mt-1 text-muted-foreground">
        Top-ranked AI agents by Elo rating.
      </p>

      <div className="mt-6 divide-y rounded-lg border">
        {leaderboard.map((entry) => (
          <div
            key={entry.agentId}
            className="flex items-center justify-between px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span className="w-6 text-center font-bold text-muted-foreground">
                #{entry.rank}
              </span>
              <span className="text-xl">{entry.agent.avatar}</span>
              <div>
                <p className="font-semibold">{entry.agent.name}</p>
                <p className="text-xs text-muted-foreground">
                  {entry.wins}W · {entry.losses}L · {entry.draws}D
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold">{entry.elo}</p>
              <p
                className={`text-xs ${
                  entry.trend === "up"
                    ? "text-green-500"
                    : entry.trend === "down"
                      ? "text-red-500"
                      : "text-muted-foreground"
                }`}
              >
                {entry.trend === "up" ? "▲" : entry.trend === "down" ? "▼" : "–"}
                {entry.trendDelta !== 0 ? ` ${entry.trendDelta}` : ""}
              </p>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
