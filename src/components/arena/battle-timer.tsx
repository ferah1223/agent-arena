"use client";

import { useEffect, useState } from "react";

interface BattleTimerProps {
  /** Total seconds for the round */
  totalSeconds: number;
  /** Whether the timer is actively counting down */
  running: boolean;
  /** Called when the timer reaches zero */
  onExpire?: () => void;
}

export function BattleTimer({
  totalSeconds,
  running,
  onExpire,
}: BattleTimerProps) {
  const [remaining, setRemaining] = useState(totalSeconds);

  useEffect(() => {
    setRemaining(totalSeconds);
  }, [totalSeconds]);

  useEffect(() => {
    if (!running || remaining <= 0) return;

    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onExpire?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [running, remaining, onExpire]);

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  const pct = (remaining / totalSeconds) * 100;
  const isLow = remaining <= 10;

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={cn(
          "font-mono text-3xl font-bold tabular-nums",
          isLow ? "text-red-500 animate-pulse" : "text-foreground",
        )}
      >
        {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
      </div>
      <div className="h-1.5 w-32 overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full transition-all duration-1000",
            isLow ? "bg-red-500" : "bg-primary",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
