"use client";
import type { BattlePokemon } from "@/src/hooks/useBattleWS";

interface TeamDotsProps {
  team: BattlePokemon[];
  activeIndex: number;
  color?: string;
}

export function TeamDots({ team, activeIndex, color = "#6c63ff" }: TeamDotsProps) {
  return (
    <div className="flex items-center gap-1">
      {team.map((mon, i) => {
        const isActive = i === activeIndex;
        const isFainted = mon.fainted;
        return (
          <div
            key={i}
            className="w-3 h-3 rounded-full transition-all duration-200"
            style={{
              backgroundColor: isFainted
                ? "rgba(255,255,255,0.08)"
                : isActive
                ? color
                : `${color}50`,
              border: isActive && !isFainted ? `2px solid ${color}` : "2px solid transparent",
              boxShadow: isActive && !isFainted ? `0 0 6px ${color}60` : "none",
            }}
          />
        );
      })}
    </div>
  );
}
