"use client";
import { useState } from "react";
import { PokemonSprite } from "./PokemonSprite";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import type { BattlePokemon } from "@/src/hooks/useBattleWS";

interface TeamPreviewProps {
  myTeam: BattlePokemon[];
  opponentTeam: BattlePokemon[];
  waitingForOpponent: boolean;
  onSelectLead: (index: number) => void;
}

export function TeamPreview({
  myTeam,
  opponentTeam,
  waitingForOpponent,
  onSelectLead,
}: TeamPreviewProps) {
  const [selectedLead, setSelectedLead] = useState(0);
  const [confirmed, setConfirmed] = useState(false);

  function handleConfirm() {
    if (confirmed) return;
    setConfirmed(true);
    onSelectLead(selectedLead);
  }

  return (
    <div className="max-w-[1100px] mx-auto px-6 py-8 flex flex-col items-center gap-8 min-h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="text-center">
        <p
          className="text-[10px] text-text-muted tracking-[0.4em] mb-2"
          style={{ fontFamily: "var(--font-jetbrains)" }}
        >
          {"// TEAM PREVIEW"}
        </p>
        <h1
          className="text-3xl font-black text-text-primary tracking-tight"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          {confirmed ? "WAITING FOR OPPONENT" : "CHOOSE YOUR LEAD"}
        </h1>
        <p
          className="text-sm text-text-secondary mt-2 max-w-md"
          style={{ fontFamily: "var(--font-dm-sans)" }}
        >
          {confirmed
            ? "Your opponent is still selecting their lead Pokémon."
            : "Select which Pokémon to send out first. You can see your opponent's team below."}
        </p>
      </div>

      {/* Opponent team (compact) */}
      <div className="w-full max-w-[800px]">
        <p
          className="text-[8px] font-bold tracking-[0.25em] text-text-muted mb-2"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          OPPONENT&apos;S TEAM
        </p>
        <div
          className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden"
        >
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-px" style={{ backgroundColor: "var(--bg-border)" }}>
            {opponentTeam.map((mon, i) => (
              <div
                key={i}
                className="flex flex-col items-center py-3 px-2 gap-1"
                style={{ backgroundColor: "var(--bg-surface)" }}
              >
                <PokemonSprite
                  speciesId={mon.species_id}
                  name={mon.name}
                  size={56}
                />
                <span
                  className="text-[9px] font-medium text-text-primary capitalize text-center truncate w-full"
                  style={{ fontFamily: "var(--font-dm-sans)" }}
                >
                  {mon.name.replace(/-/g, " ")}
                </span>
                <div className="flex gap-0.5">
                  {mon.types.map((t) => (
                    <TypeBadge key={t} type={t} size="sm" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3 w-full max-w-[800px]">
        <div className="flex-1 h-px" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
        <span
          className="text-[10px] font-bold text-text-muted"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          VS
        </span>
        <div className="flex-1 h-px" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
      </div>

      {/* My team (selectable) */}
      <div className="w-full max-w-[800px]">
        <p
          className="text-[8px] font-bold tracking-[0.25em] mb-2"
          style={{
            fontFamily: "var(--font-unbounded)",
            color: "#f87171",
          }}
        >
          YOUR TEAM — SELECT LEAD
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {myTeam.map((mon, i) => {
            const isSelected = selectedLead === i;
            return (
              <button
                key={i}
                onClick={() => !confirmed && setSelectedLead(i)}
                disabled={confirmed}
                className="relative rounded-xl border text-left p-3 transition-all group"
                style={{
                  backgroundColor: isSelected
                    ? "rgba(248,113,113,0.08)"
                    : "var(--bg-surface)",
                  borderColor: isSelected
                    ? "rgba(248,113,113,0.4)"
                    : "var(--bg-border)",
                  cursor: confirmed ? "not-allowed" : "pointer",
                  boxShadow: isSelected
                    ? "0 0 20px rgba(248,113,113,0.08), inset 0 0 30px rgba(248,113,113,0.03)"
                    : "none",
                }}
              >
                {/* Lead badge */}
                {isSelected && (
                  <div
                    className="absolute -top-2 left-3 px-2 py-0.5 rounded-full text-[7px] font-bold tracking-wider"
                    style={{
                      fontFamily: "var(--font-jetbrains)",
                      backgroundColor: "#f87171",
                      color: "#080810",
                    }}
                  >
                    LEAD
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <PokemonSprite
                    speciesId={mon.species_id}
                    name={mon.name}
                    size={64}
                  />
                  <div className="flex-1 min-w-0">
                    <span
                      className="text-xs font-medium text-text-primary capitalize block truncate group-hover:text-white transition-colors"
                      style={{ fontFamily: "var(--font-dm-sans)" }}
                    >
                      {mon.name.replace(/-/g, " ")}
                    </span>
                    <div className="flex gap-0.5 mt-1">
                      {mon.types.map((t) => (
                        <TypeBadge key={t} type={t} size="sm" />
                      ))}
                    </div>
                    {(mon.ability || mon.item) && (
                      <p
                        className="text-[8px] text-text-muted capitalize mt-1 truncate"
                        style={{ fontFamily: "var(--font-jetbrains)" }}
                      >
                        {mon.ability ? mon.ability.replace(/-/g, " ") : ""}
                        {mon.ability && mon.item ? " · " : ""}
                        {mon.item ? mon.item.replace(/-/g, " ") : ""}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Confirm button */}
      {confirmed ? (
        <div className="flex flex-col items-center gap-3">
          <div className="relative w-14 h-14">
            <div
              className="absolute inset-0 rounded-full border-2 animate-spin"
              style={{
                borderColor: "rgba(248,113,113,0.15)",
                borderTopColor: "rgba(248,113,113,0.6)",
                animationDuration: "1.2s",
              }}
            />
            <div
              className="absolute inset-2 rounded-full border animate-spin"
              style={{
                borderColor: "rgba(248,113,113,0.08)",
                borderTopColor: "rgba(248,113,113,0.3)",
                animationDuration: "2s",
                animationDirection: "reverse",
              }}
            />
          </div>
          <span
            className="text-[9px] text-text-muted tracking-wider"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            WAITING FOR OPPONENT...
          </span>
        </div>
      ) : (
        <button
          onClick={handleConfirm}
          className="px-8 py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2"
          style={{
            fontFamily: "var(--font-unbounded)",
            backgroundColor: "rgba(248,113,113,0.15)",
            border: "1px solid rgba(248,113,113,0.4)",
            color: "#f87171",
          }}
        >
          CONFIRM LEAD: {myTeam[selectedLead]?.name.replace(/-/g, " ").toUpperCase()}
        </button>
      )}
    </div>
  );
}
