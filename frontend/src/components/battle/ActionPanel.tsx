"use client";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import type { BattleMoveSlot } from "@/src/hooks/useBattleWS";

// Type colors matching the app's TypeBadge palette
const TYPE_BG: Record<string, string> = {
  normal: "#9ca3af", fire: "#f97316", water: "#3b82f6", electric: "#eab308",
  grass: "#22c55e", ice: "#06b6d4", fighting: "#ef4444", poison: "#a855f7",
  ground: "#d97706", flying: "#818cf8", psychic: "#ec4899", bug: "#84cc16",
  rock: "#78716c", ghost: "#6366f1", dragon: "#8b5cf6", dark: "#374151",
  steel: "#94a3b8", fairy: "#f472b6",
};

interface ActionPanelProps {
  moves: BattleMoveSlot[];
  disabled?: boolean;
  waitingForOpponent?: boolean;
  onSelectMove: (index: number) => void;
}

export function ActionPanel({ moves, disabled, waitingForOpponent, onSelectMove }: ActionPanelProps) {
  const slots = Array(4).fill(null).map((_, i) => moves[i] ?? null);

  return (
    <div className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden">
      <div className="px-3 py-1.5 border-b border-bg-border flex items-center justify-between">
        <span
          className="text-[8px] font-bold text-text-muted tracking-[0.25em]"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          {waitingForOpponent ? "WAITING FOR OPPONENT..." : disabled ? "OPPONENT'S TURN" : "CHOOSE A MOVE"}
        </span>
        {waitingForOpponent && (
          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
        )}
      </div>

      <div className="grid grid-cols-2 gap-1 p-2">
        {slots.map((move, i) => {
          if (!move) {
            return (
              <div
                key={i}
                className="h-12 rounded-lg border border-bg-border bg-bg-elevated opacity-20"
              />
            );
          }

          const typeColor = TYPE_BG[move.type] ?? "#6b7280";
          const isDisabled = disabled || waitingForOpponent;

          return (
            <button
              key={i}
              onClick={() => !isDisabled && onSelectMove(i)}
              disabled={isDisabled}
              className="h-12 rounded-lg border text-left px-3 flex flex-col justify-center gap-0.5 transition-all group"
              style={{
                backgroundColor: `${typeColor}18`,
                borderColor: `${typeColor}35`,
                cursor: isDisabled ? "not-allowed" : "pointer",
                opacity: isDisabled ? 0.5 : 1,
              }}
            >
              <div className="flex items-center justify-between gap-1">
                <span
                  className="text-[10px] font-medium text-text-primary capitalize truncate group-hover:text-white transition-colors"
                  style={{ fontFamily: "var(--font-dm-sans)" }}
                >
                  {move.name.replace(/-/g, " ")}
                </span>
                <TypeBadge type={move.type} size="sm" />
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="text-[8px] tabular-nums"
                  style={{ fontFamily: "var(--font-jetbrains)", color: typeColor }}
                >
                  {move.power > 0 ? `${move.power} PWR` : "—"}
                </span>
                <span
                  className="text-[8px] tabular-nums text-text-muted"
                  style={{ fontFamily: "var(--font-jetbrains)" }}
                >
                  {move.accuracy}% ACC
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
