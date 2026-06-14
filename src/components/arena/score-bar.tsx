"use client";

interface ScoreBarProps {
  labelA: string;
  labelB: string;
  scoreA: number;
  scoreB: number;
  eloDeltaA?: number;
  eloDeltaB?: number;
}

export function ScoreBar({
  labelA,
  labelB,
  scoreA,
  scoreB,
  eloDeltaA,
  eloDeltaB,
}: ScoreBarProps) {
  const total = scoreA + scoreB || 1;
  const percentA = (scoreA / total) * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm font-medium">
        <span>
          {labelA}
          {eloDeltaA !== undefined && (
            <span className={eloDeltaA >= 0 ? "text-green-500" : "text-red-500"}>
              {" "}
              ({eloDeltaA >= 0 ? "+" : ""}
              {eloDeltaA})
            </span>
          )}
        </span>
        <span>
          {labelB}
          {eloDeltaB !== undefined && (
            <span className={eloDeltaB >= 0 ? "text-green-500" : "text-red-500"}>
              {" "}
              ({eloDeltaB >= 0 ? "+" : ""}
              {eloDeltaB})
            </span>
          )}
        </span>
      </div>
      <div className="flex h-3 overflow-hidden rounded-full bg-muted">
        <div
          className="bg-primary transition-all duration-500"
          style={{ width: `${percentA}%` }}
        />
        <div
          className="bg-destructive transition-all duration-500"
          style={{ width: `${100 - percentA}%` }}
        />
      </div>
      <div className="flex justify-between text-lg font-bold tabular-nums">
        <span>{scoreA}</span>
        <span>{scoreB}</span>
      </div>
    </div>
  );
}
