"use client";
import type { BattlePokemon } from "@/src/hooks/useBattleWS";

interface TeamDotsProps {
  team: BattlePokemon[];
  activeIndex: number;
  color?: string;
}

export function TeamDots({
  team,
  activeIndex,
  color = "#6c63ff",
}: TeamDotsProps) {
  return (
    <div className="flex items-center gap-1">
      {team.map((mon, i) => {
        const isActive = i === activeIndex;
        const isFainted = mon.fainted;
        return (
          <div
            key={i}
            className="w-3 h-3 rounded-full flex items-center justify-center transition-all duration-200"
            style={{
              backgroundColor: isFainted
                ? "rgba(248,113,113,0.12)"
                : isActive
                  ? color
                  : `${color}40`,
              border: isFainted
                ? "1.5px solid rgba(248,113,113,0.35)"
                : isActive
                  ? `2px solid ${color}`
                  : "2px solid transparent",
              boxShadow:
                isActive && !isFainted ? `0 0 6px ${color}60` : "none",
            }}
          >
            {isFainted && (
              <span
                className="text-[5px] font-black leading-none"
                style={{ color: "#f87171" }}
              >
                +
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
