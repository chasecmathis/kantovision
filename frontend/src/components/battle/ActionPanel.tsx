"use client";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { MoveTimer } from "@/src/components/battle/MoveTimer";
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
  /** Changes each turn — used to reset the move timer. Pass battleState.turn. */
  turnKey: number;
  /** Seconds per turn, matching backend move_timeout_seconds (default 60). */
  timerSeconds?: number;
  /** Epoch seconds (from backend) when the current turn timer started. */
  turnStartedAt?: number | null;
}

export function ActionPanel({
  moves,
  disabled,
  waitingForOpponent,
  onSelectMove,
  turnKey,
  timerSeconds = 60,
  turnStartedAt,
}: ActionPanelProps) {
  const initialSeconds = turnStartedAt != null
    ? Math.max(0, timerSeconds - Math.floor(Date.now() / 1000 - turnStartedAt))
    : timerSeconds;
  const slots = Array(4).fill(null).map((_, i) => moves[i] ?? null);
  const isMyTurn = !disabled && !waitingForOpponent;

  let headerLabel: string;
  if (waitingForOpponent) headerLabel = "WAITING FOR OPPONENT...";
  else if (disabled) headerLabel = "OPPONENT'S TURN";
  else headerLabel = "CHOOSE A MOVE";

  return (
    <div className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden">
      {/* Header */}
      <div className="px-3 py-1.5 border-b border-bg-border flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className="text-[8px] font-bold text-text-muted tracking-[0.25em] truncate"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            {headerLabel}
          </span>
          {waitingForOpponent && (
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse shrink-0" />
          )}
        </div>

        {/* Move timer — only visible when it's the player's turn */}
        <div
          style={{
            opacity: isMyTurn ? 1 : 0,
            transition: "opacity 0.3s ease",
            pointerEvents: "none",
          }}
        >
          <MoveTimer
            key={turnKey}
            totalSeconds={timerSeconds}
            initialSeconds={initialSeconds}
            active={isMyTurn}
          />
        </div>
      </div>

      {/* Move grid */}
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
