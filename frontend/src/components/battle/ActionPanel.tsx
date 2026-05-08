"use client";
import { useState } from "react";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { MoveTimer } from "@/src/components/battle/MoveTimer";
import { HPBar } from "@/src/components/battle/HPBar";
import type { BattleMoveSlot, BattlePokemon } from "@/src/hooks/useBattleWS";

// ─── Constants ───────────────────────────────────────────────────────────────

const TYPE_BG: Record<string, string> = {
  normal: "#9ca3af",
  fire: "#f97316",
  water: "#3b82f6",
  electric: "#eab308",
  grass: "#22c55e",
  ice: "#06b6d4",
  fighting: "#ef4444",
  poison: "#a855f7",
  ground: "#d97706",
  flying: "#818cf8",
  psychic: "#ec4899",
  bug: "#84cc16",
  rock: "#78716c",
  ghost: "#6366f1",
  dragon: "#8b5cf6",
  dark: "#374151",
  steel: "#94a3b8",
  fairy: "#f472b6",
};

const STATUS_LABEL: Record<string, { text: string; color: string }> = {
  burn: { text: "BRN", color: "#f97316" },
  paralysis: { text: "PAR", color: "#eab308" },
  poison: { text: "PSN", color: "#a855f7" },
  toxic: { text: "TOX", color: "#7c3aed" },
  sleep: { text: "SLP", color: "#94a3b8" },
  freeze: { text: "FRZ", color: "#06b6d4" },
};

const CATEGORY_STYLE: Record<string, { label: string; color: string }> = {
  physical: { label: "PHY", color: "#f97316" },
  special: { label: "SPC", color: "#60a5fa" },
  status: { label: "STA", color: "#94a3b8" },
};

// ─── ActionPanel ─────────────────────────────────────────────────────────────

interface ActionPanelProps {
  moves: BattleMoveSlot[];
  team: BattlePokemon[];
  activeIndex: number;
  disabled?: boolean;
  waitingForOpponent?: boolean;
  onSelectMove: (index: number) => void;
  onSelectSwitch: (index: number) => void;
  turnKey: number;
  timerSeconds?: number;
  turnStartedAt?: number | null;
}

export function ActionPanel({
  moves,
  team,
  activeIndex,
  disabled,
  waitingForOpponent,
  onSelectMove,
  onSelectSwitch,
  turnKey,
  timerSeconds = 60,
  turnStartedAt,
}: ActionPanelProps) {
  const [tab, setTab] = useState<"moves" | "switch">("moves");
  const initialSeconds =
    turnStartedAt != null
      ? Math.max(
          0,
          timerSeconds - Math.floor(Date.now() / 1000 - turnStartedAt),
        )
      : timerSeconds;
  const isMyTurn = !disabled && !waitingForOpponent;

  let headerLabel: string;
  if (waitingForOpponent) headerLabel = "WAITING FOR OPPONENT\u2026";
  else if (disabled) headerLabel = "OPPONENT\u2019S TURN";
  else headerLabel = tab === "moves" ? "CHOOSE A MOVE" : "SWITCH POKEMON";

  const hasBench = team.some((mon, i) => i !== activeIndex && !mon.fainted);

  return (
    <div className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden">
      {/* Header */}
      <div
        className="px-3 py-1.5 border-b border-bg-border flex items-center justify-between gap-2"
        style={{
          backgroundColor: waitingForOpponent
            ? "rgba(108,99,255,0.03)"
            : undefined,
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          {waitingForOpponent && (
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inset-0 rounded-full bg-accent/40" />
              <span className="relative rounded-full h-2 w-2 bg-accent" />
            </span>
          )}
          <span
            className="text-[8px] font-bold text-text-muted tracking-[0.25em] truncate"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            {headerLabel}
          </span>
        </div>

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

      {/* Tabs */}
      <div className="flex border-b border-bg-border">
        <button
          onClick={() => setTab("moves")}
          className="flex-1 py-1.5 text-[9px] font-bold tracking-[0.15em] transition-all"
          style={{
            fontFamily: "var(--font-unbounded)",
            color:
              tab === "moves" ? "var(--accent)" : "var(--text-muted)",
            borderBottom:
              tab === "moves"
                ? "2px solid var(--accent)"
                : "2px solid transparent",
            backgroundColor:
              tab === "moves" ? "rgba(108,99,255,0.06)" : "transparent",
          }}
        >
          MOVES
        </button>
        <button
          onClick={() => setTab("switch")}
          disabled={!hasBench}
          className="flex-1 py-1.5 text-[9px] font-bold tracking-[0.15em] transition-all"
          style={{
            fontFamily: "var(--font-unbounded)",
            color: !hasBench
              ? "var(--text-muted)"
              : tab === "switch"
                ? "var(--accent)"
                : "var(--text-muted)",
            borderBottom:
              tab === "switch"
                ? "2px solid var(--accent)"
                : "2px solid transparent",
            backgroundColor:
              tab === "switch" ? "rgba(108,99,255,0.06)" : "transparent",
            opacity: hasBench ? 1 : 0.35,
            cursor: hasBench ? "pointer" : "not-allowed",
          }}
        >
          SWITCH
        </button>
      </div>

      {/* Content */}
      {tab === "moves" ? (
        <MoveGrid
          moves={moves}
          disabled={disabled}
          waitingForOpponent={waitingForOpponent}
          onSelectMove={onSelectMove}
        />
      ) : (
        <SwitchGrid
          team={team}
          activeIndex={activeIndex}
          disabled={disabled}
          waitingForOpponent={waitingForOpponent}
          onSelectSwitch={onSelectSwitch}
        />
      )}
    </div>
  );
}

// ─── Move Grid ───────────────────────────────────────────────────────────────

function MoveGrid({
  moves,
  disabled,
  waitingForOpponent,
  onSelectMove,
}: {
  moves: BattleMoveSlot[];
  disabled?: boolean;
  waitingForOpponent?: boolean;
  onSelectMove: (index: number) => void;
}) {
  const slots = Array(4)
    .fill(null)
    .map((_, i) => moves[i] ?? null);
  const isDisabled = disabled || waitingForOpponent;

  return (
    <div className="grid grid-cols-2 gap-1 p-2">
      {slots.map((move, i) => {
        if (!move) {
          return (
            <div
              key={i}
              className="h-14 rounded-lg border border-bg-border bg-bg-elevated opacity-15"
            />
          );
        }

        const typeColor = TYPE_BG[move.type] ?? "#6b7280";
        const catStyle = CATEGORY_STYLE[move.category] ?? CATEGORY_STYLE.status;
        const ppRatio = move.max_pp > 0 ? move.current_pp / move.max_pp : 1;
        const ppColor =
          move.current_pp === 0
            ? "#ef4444"
            : ppRatio <= 0.25
              ? "#eab308"
              : "var(--text-muted)";

        return (
          <button
            key={i}
            onClick={() => !isDisabled && onSelectMove(i)}
            disabled={isDisabled}
            className="move-card h-14 rounded-lg border text-left px-3 flex flex-col justify-center gap-1 group"
            style={{
              backgroundColor: `${typeColor}10`,
              borderColor: `${typeColor}28`,
              cursor: isDisabled ? "not-allowed" : "pointer",
              opacity: isDisabled ? 0.45 : 1,
            }}
          >
            {/* Row 1: Name + type */}
            <div className="flex items-center justify-between gap-1">
              <span
                className="text-[10px] font-medium text-text-primary capitalize truncate group-hover:text-white transition-colors"
                style={{ fontFamily: "var(--font-dm-sans)" }}
              >
                {move.name.replace(/-/g, " ")}
              </span>
              <TypeBadge type={move.type} size="sm" />
            </div>

            {/* Row 2: Category + Priority + Power · Acc · PP */}
            <div className="flex items-center gap-1">
              {/* Category badge */}
              <span
                className="text-[6px] font-bold px-1 py-px rounded leading-none"
                style={{
                  fontFamily: "var(--font-jetbrains)",
                  backgroundColor: `${catStyle.color}15`,
                  color: catStyle.color,
                  border: `1px solid ${catStyle.color}25`,
                }}
              >
                {catStyle.label}
              </span>

              {/* Priority indicator */}
              {move.priority > 0 && (
                <span
                  className="text-[6px] font-bold px-1 py-px rounded leading-none"
                  style={{
                    fontFamily: "var(--font-jetbrains)",
                    backgroundColor: "rgba(251,191,36,0.1)",
                    color: "#fbbf24",
                    border: "1px solid rgba(251,191,36,0.2)",
                  }}
                >
                  +{move.priority}
                </span>
              )}

              <div className="flex-1" />

              {/* Power */}
              <span
                className="text-[8px] tabular-nums"
                style={{
                  fontFamily: "var(--font-jetbrains)",
                  color: typeColor,
                }}
              >
                {move.power > 0 ? move.power : "\u2014"}
              </span>

              <span
                className="text-[5px] text-text-muted"
                style={{ opacity: 0.4 }}
              >
                {"\u00b7"}
              </span>

              {/* Accuracy */}
              <span
                className="text-[8px] tabular-nums text-text-muted"
                style={{ fontFamily: "var(--font-jetbrains)" }}
              >
                {move.accuracy > 0 ? `${move.accuracy}` : "\u2014"}
              </span>

              <span
                className="text-[5px] text-text-muted"
                style={{ opacity: 0.4 }}
              >
                {"\u00b7"}
              </span>

              {/* PP with color coding */}
              <span
                className="text-[8px] tabular-nums"
                style={{
                  fontFamily: "var(--font-jetbrains)",
                  color: ppColor,
                }}
              >
                {move.current_pp}/{move.max_pp}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ─── Switch Grid ─────────────────────────────────────────────────────────────

function SwitchGrid({
  team,
  activeIndex,
  disabled,
  waitingForOpponent,
  onSelectSwitch,
}: {
  team: BattlePokemon[];
  activeIndex: number;
  disabled?: boolean;
  waitingForOpponent?: boolean;
  onSelectSwitch: (index: number) => void;
}) {
  const isDisabled = disabled || waitingForOpponent;

  return (
    <div className="flex flex-col gap-1 p-2">
      {team.map((mon, i) => {
        const isActive = i === activeIndex;
        const isFainted = mon.fainted;
        const canSwitch = !isActive && !isFainted && !isDisabled;
        const statusInfo =
          mon.status && mon.status !== "none" ? STATUS_LABEL[mon.status] : null;

        return (
          <button
            key={i}
            onClick={() => canSwitch && onSelectSwitch(i)}
            disabled={!canSwitch}
            className="switch-card h-12 rounded-lg border text-left px-3 flex items-center gap-3 group"
            style={{
              backgroundColor: isActive
                ? "rgba(108,99,255,0.08)"
                : isFainted
                  ? "rgba(239,68,68,0.04)"
                  : "var(--bg-elevated)",
              borderColor: isActive
                ? "rgba(108,99,255,0.25)"
                : isFainted
                  ? "rgba(239,68,68,0.15)"
                  : "var(--bg-border)",
              cursor: canSwitch ? "pointer" : "not-allowed",
              opacity: isFainted ? 0.4 : isActive ? 0.55 : isDisabled ? 0.45 : 1,
            }}
          >
            {/* Dex number */}
            <div
              className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 text-[9px] font-bold"
              style={{
                backgroundColor: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.06)",
                fontFamily: "var(--font-jetbrains)",
                color: "var(--text-muted)",
              }}
            >
              {String(mon.species_id).padStart(3, "0")}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span
                  className="text-[10px] font-medium text-text-primary capitalize truncate group-hover:text-white transition-colors"
                  style={{ fontFamily: "var(--font-dm-sans)" }}
                >
                  {mon.name.replace(/-/g, " ")}
                </span>
                {mon.types.map((t) => (
                  <TypeBadge key={t} type={t} size="sm" />
                ))}
                {statusInfo && (
                  <span
                    className="text-[6.5px] font-bold px-1 py-0.5 rounded"
                    style={{
                      backgroundColor: `${statusInfo.color}20`,
                      color: statusInfo.color,
                      fontFamily: "var(--font-jetbrains)",
                    }}
                  >
                    {statusInfo.text}
                  </span>
                )}
                {isActive && (
                  <span
                    className="text-[6.5px] font-bold px-1 py-0.5 rounded"
                    style={{
                      backgroundColor: "rgba(108,99,255,0.12)",
                      color: "var(--accent)",
                      fontFamily: "var(--font-jetbrains)",
                    }}
                  >
                    IN
                  </span>
                )}
              </div>
              {(mon.ability || mon.item) && (
                <span
                  className="text-[7px] text-text-muted capitalize"
                  style={{ fontFamily: "var(--font-jetbrains)" }}
                >
                  {mon.ability ? mon.ability.replace(/-/g, " ") : ""}
                  {mon.ability && mon.item ? " \u00b7 " : ""}
                  {mon.item ? mon.item.replace(/-/g, " ") : ""}
                </span>
              )}

              {/* HP bar */}
              <div className="flex items-center gap-1.5 mt-0.5">
                <div className="flex-1">
                  <HPBar
                    current={mon.current_hp}
                    max={mon.max_hp}
                    size="sm"
                  />
                </div>
                <span
                  className="text-[7px] tabular-nums text-text-muted shrink-0"
                  style={{ fontFamily: "var(--font-jetbrains)" }}
                >
                  {mon.current_hp}/{mon.max_hp}
                </span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
