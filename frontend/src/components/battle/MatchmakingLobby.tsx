"use client";
import { useEffect, useState } from "react";
import { Swords, ChevronDown } from "lucide-react";
import { useSavedTeams } from "@/src/hooks/useTeams";
import type { BattlePhase } from "@/src/hooks/useBattleWS";
import type { SavedTeam } from "@/src/lib/api";

interface MatchmakingLobbyProps {
  phase: BattlePhase;
  onFindBattle: (teamId: string) => void;
  onCancel: () => void;
}

export function MatchmakingLobby({ phase, onFindBattle, onCancel }: MatchmakingLobbyProps) {
  const { data: teams = [], isLoading } = useSavedTeams();
  const [selectedTeamId, setSelectedTeamId] = useState<string>("");

  // Auto-select first team
  useEffect(() => {
    if (teams.length > 0 && !selectedTeamId) {
      setSelectedTeamId(teams[0].id);
    }
  }, [teams, selectedTeamId]);

  const isQueued = phase === "queued" || phase === "matched";
  const isConnecting = phase === "connecting";

  function filledSlots(t: SavedTeam) {
    return t.slots.filter(Boolean).length;
  }

  return (
    <div className="max-w-lg mx-auto flex flex-col items-center gap-8 py-16 px-4">
      {/* Icon */}
      <div className="relative">
        <div
          className="w-20 h-20 rounded-2xl flex items-center justify-center"
          style={{ backgroundColor: "rgba(108,99,255,0.12)", border: "1px solid rgba(108,99,255,0.25)" }}
        >
          <Swords size={36} className="text-accent" strokeWidth={1.5} />
        </div>
        {isQueued && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-60" />
            <span className="relative inline-flex rounded-full h-4 w-4 bg-accent" />
          </span>
        )}
      </div>

      {/* Title */}
      <div className="text-center">
        <p
          className="text-[10px] text-text-muted tracking-[0.3em] mb-2"
          style={{ fontFamily: "var(--font-jetbrains)" }}
        >
          // MATCHMAKING
        </p>
        <h1
          className="text-3xl font-black text-text-primary tracking-tight"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          {isQueued ? "SEARCHING..." : "FIND A BATTLE"}
        </h1>
        <p className="text-sm text-text-secondary mt-2" style={{ fontFamily: "var(--font-dm-sans)" }}>
          {isQueued
            ? "Waiting for an opponent to join the queue."
            : "Select a saved team and challenge another trainer."}
        </p>
      </div>

      {/* Team selector */}
      {!isQueued && (
        <div className="w-full space-y-2">
          <label
            className="text-[9px] font-bold text-text-muted tracking-[0.2em]"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            SELECT TEAM
          </label>

          {isLoading ? (
            <div className="h-11 rounded-xl bg-bg-elevated border border-bg-border animate-pulse" />
          ) : teams.length === 0 ? (
            <div className="rounded-xl border border-bg-border bg-bg-elevated px-4 py-3 text-center">
              <p className="text-xs text-text-muted" style={{ fontFamily: "var(--font-dm-sans)" }}>
                No saved teams.{" "}
                <a href="/team" className="text-accent hover:underline">
                  Build one first →
                </a>
              </p>
            </div>
          ) : (
            <div className="relative">
              <select
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
                className="w-full appearance-none rounded-xl border border-bg-border bg-bg-elevated px-4 py-3 text-sm text-text-primary pr-10 focus:outline-none focus:border-accent/50 transition-colors"
                style={{ fontFamily: "var(--font-dm-sans)" }}
              >
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({filledSlots(t)}/6 Pokémon)
                  </option>
                ))}
              </select>
              <ChevronDown
                size={14}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
              />
            </div>
          )}
        </div>
      )}

      {/* CTA */}
      {isQueued ? (
        <div className="flex flex-col items-center gap-4 w-full">
          {/* Animated ring */}
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 rounded-full border-2 border-accent/20 animate-spin" style={{ borderTopColor: "rgba(108,99,255,0.7)", animationDuration: "1.2s" }} />
            <div className="absolute inset-2 rounded-full border border-accent/10 animate-spin" style={{ borderTopColor: "rgba(108,99,255,0.4)", animationDuration: "2s", animationDirection: "reverse" }} />
            <div className="absolute inset-4 rounded-full bg-accent/10 flex items-center justify-center">
              <Swords size={14} className="text-accent" />
            </div>
          </div>

          <button
            onClick={onCancel}
            className="px-5 py-2 rounded-lg border border-bg-border bg-bg-elevated text-sm text-text-secondary hover:text-text-primary hover:border-accent/30 transition-all"
            style={{ fontFamily: "var(--font-dm-sans)" }}
          >
            Cancel Search
          </button>
        </div>
      ) : (
        <button
          onClick={() => selectedTeamId && onFindBattle(selectedTeamId)}
          disabled={!selectedTeamId || teams.length === 0 || isConnecting}
          className="w-full py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            fontFamily: "var(--font-unbounded)",
            backgroundColor: "rgba(108,99,255,0.15)",
            border: "1px solid rgba(108,99,255,0.35)",
            color: "#6c63ff",
          }}
        >
          <Swords size={14} />
          {isConnecting ? "CONNECTING..." : "FIND BATTLE"}
        </button>
      )}
    </div>
  );
}
