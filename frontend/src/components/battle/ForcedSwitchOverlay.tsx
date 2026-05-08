"use client";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { HPBar } from "./HPBar";
import type { BattlePokemon, ForcedSwitchOption } from "@/src/hooks/useBattleWS";

const STATUS_LABEL: Record<string, { text: string; color: string }> = {
  burn: { text: "BRN", color: "#f97316" },
  paralysis: { text: "PAR", color: "#eab308" },
  poison: { text: "PSN", color: "#a855f7" },
  toxic: { text: "TOX", color: "#7c3aed" },
  sleep: { text: "SLP", color: "#94a3b8" },
  freeze: { text: "FRZ", color: "#06b6d4" },
};

interface ForcedSwitchOverlayProps {
  team: BattlePokemon[];
  options: ForcedSwitchOption[];
  onSubmitSwitch: (index: number) => void;
}

export function ForcedSwitchOverlay({
  team,
  options,
  onSubmitSwitch,
}: ForcedSwitchOverlayProps) {
  const availableIndices = new Set(options.map((o) => o.index));

  return (
    <div className="rounded-xl border overflow-hidden animate-fade-in"
      style={{
        borderColor: "rgba(248,113,113,0.35)",
        backgroundColor: "rgba(248,113,113,0.04)",
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-2.5 border-b flex items-center gap-2"
        style={{
          borderColor: "rgba(248,113,113,0.2)",
          backgroundColor: "rgba(248,113,113,0.06)",
        }}
      >
        <div
          className="w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: "#f87171" }}
        />
        <span
          className="text-[9px] font-bold tracking-[0.25em]"
          style={{
            fontFamily: "var(--font-unbounded)",
            color: "#f87171",
          }}
        >
          CHOOSE A REPLACEMENT
        </span>
      </div>

      {/* Pokemon options */}
      <div className="flex flex-col gap-1 p-2">
        {team.map((mon, i) => {
          const isAvailable = availableIndices.has(i);
          const isFainted = mon.fainted;
          const hpPercent = mon.max_hp > 0 ? (mon.current_hp / mon.max_hp) * 100 : 0;
          const hpColor = hpPercent > 50 ? "#22c55e" : hpPercent > 20 ? "#eab308" : "#ef4444";
          const statusInfo = mon.status && mon.status !== "none" ? STATUS_LABEL[mon.status] : null;

          if (isFainted) return null;

          return (
            <button
              key={i}
              onClick={() => isAvailable && onSubmitSwitch(i)}
              disabled={!isAvailable}
              className="h-14 rounded-lg border text-left px-3 flex items-center gap-3 transition-all group"
              style={{
                backgroundColor: isAvailable
                  ? "rgba(248,113,113,0.06)"
                  : "var(--bg-elevated)",
                borderColor: isAvailable
                  ? "rgba(248,113,113,0.25)"
                  : "var(--bg-border)",
                cursor: isAvailable ? "pointer" : "not-allowed",
                opacity: isAvailable ? 1 : 0.35,
              }}
            >
              {/* Sprite placeholder */}
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-[9px] font-bold"
                style={{
                  backgroundColor: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.1)",
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
                    className="text-[11px] font-medium text-text-primary capitalize truncate group-hover:text-white transition-colors"
                    style={{ fontFamily: "var(--font-dm-sans)" }}
                  >
                    {mon.name.replace(/-/g, " ")}
                  </span>
                  {mon.types.map((t) => (
                    <TypeBadge key={t} type={t} size="sm" />
                  ))}
                  {statusInfo && (
                    <span
                      className="text-[7px] font-bold px-1 py-0.5 rounded"
                      style={{
                        backgroundColor: `${statusInfo.color}20`,
                        color: statusInfo.color,
                        fontFamily: "var(--font-jetbrains)",
                      }}
                    >
                      {statusInfo.text}
                    </span>
                  )}
                </div>
                {(mon.ability || mon.item) && (
                  <span
                    className="text-[7px] text-text-muted capitalize"
                    style={{ fontFamily: "var(--font-jetbrains)" }}
                  >
                    {mon.ability ? mon.ability.replace(/-/g, " ") : ""}
                    {mon.ability && mon.item ? " · " : ""}
                    {mon.item ? mon.item.replace(/-/g, " ") : ""}
                  </span>
                )}

                {/* HP bar */}
                <div className="mt-0.5">
                  <HPBar current={mon.current_hp} max={mon.max_hp} size="sm" />
                </div>
              </div>

              {/* Send out indicator */}
              {isAvailable && (
                <div
                  className="text-[8px] font-bold px-2 py-1 rounded-md shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{
                    fontFamily: "var(--font-unbounded)",
                    backgroundColor: "rgba(248,113,113,0.15)",
                    color: "#f87171",
                    border: "1px solid rgba(248,113,113,0.3)",
                  }}
                >
                  SEND OUT
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
