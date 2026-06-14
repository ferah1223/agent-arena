"use client";

import { useEffect, useState } from "react";

interface ActivityItem {
  id: string;
  message: string;
  timestamp: string;
  type: "match-start" | "match-end" | "round-end" | "system";
}

const demoActivity: ActivityItem[] = [
  { id: "1", message: "🏆 Nova defeated Claude Phantom in Code Golf!", timestamp: "2 min ago", type: "match-end" },
  { id: "2", message: "⚔️ LlamaForge vs Cipher — Math Duel starting now", timestamp: "5 min ago", type: "match-start" },
  { id: "3", message: "📊 Round 3 complete: Echo scores 8.2 in Trivia Brawl", timestamp: "8 min ago", type: "round-end" },
  { id: "4", message: "🎉 Claude Phantom reached 1900 Elo!", timestamp: "15 min ago", type: "system" },
  { id: "5", message: "🔥 Nova is on a 7-match win streak!", timestamp: "22 min ago", type: "system" },
];

interface ActivityFeedProps {
  items?: ActivityItem[];
}

export function ActivityFeed({ items = demoActivity }: ActivityFeedProps) {
  const [visible, setVisible] = useState(items.slice(0, 3));

  useEffect(() => {
    const timer = setInterval(() => {
      setVisible((prev) => {
        const nextIdx =
          (items.indexOf(prev[prev.length - 1]) + 1) % items.length;
        const updated = [...prev.slice(1), items[nextIdx]];
        return updated;
      });
    }, 4000);
    return () => clearInterval(timer);
  }, [items]);

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
        Live Activity
      </h3>
      <ul className="space-y-1">
        {visible.map((item) => (
          <li
            key={item.id}
            className="rounded-md bg-muted/50 px-3 py-2 text-sm animate-in fade-in slide-in-from-top-1"
          >
            <span>{item.message}</span>
            <span className="ml-2 text-xs text-muted-foreground">
              {item.timestamp}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
