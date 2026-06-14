"use client";

import type { Match } from "@/lib/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface MatchCardProps {
  match: Match;
  onClick?: (matchId: string) => void;
}

export function MatchCard({ match, onClick }: MatchCardProps) {
  return (
    <Card
      className="cursor-pointer transition hover:border-primary/50"
      onClick={() => onClick?.(match.id)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span className="uppercase tracking-wide">{match.gameMode}</span>
          <span>{match.status}</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 text-center">
            <p className="text-lg font-semibold">{match.agentAId}</p>
            <p className="text-2xl font-bold">{match.agentAScore}</p>
          </div>
          <span className="text-xl font-bold text-muted-foreground">VS</span>
          <div className="flex-1 text-center">
            <p className="text-lg font-semibold">{match.agentBId}</p>
            <p className="text-2xl font-bold">{match.agentBScore}</p>
          </div>
        </div>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          {match.spectators} spectators · Round {match.currentRound}/{match.totalRounds}
        </p>
      </CardContent>
    </Card>
  );
}
