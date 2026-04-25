"use client";
import { useState } from "react";
import Link from "next/link";
import { TeamSlotStrip } from "@/src/components/team/TeamSlotStrip";
import { MemberEditor } from "@/src/components/team/MemberEditor";
import { TeamAnalysisPanel } from "@/src/components/team/TeamAnalysisPanel";
import { PokemonPickerModal } from "@/src/components/team/PokemonPickerModal";
import { SaveTeamModal } from "@/src/components/team/SaveTeamModal";
import { LoadTeamsPanel } from "@/src/components/team/LoadTeamsPanel";
import { type Team, type TeamMember, type Pokemon, createTeamMember } from "@/src/lib/pokeapi";
import type { SavedTeam } from "@/src/lib/api";
import { useAuth } from "@/src/contexts/AuthContext";
import { Save, FolderOpen, LogIn, X, ChevronDown } from "lucide-react";

export default function TeamPage() {
  const { user } = useAuth();
  const [team, setTeam] = useState<Team>(Array(6).fill(null));
  const [activeSlotIndex, setActiveSlotIndex] = useState(0);
  const [pickerOpen, setPickerOpen] = useState(false);

  // Auth-gated panels
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [loadPanelOpen, setLoadPanelOpen] = useState(false);

  // Track which saved team we're editing (for overwrite)
  const [activeSavedTeam, setActiveSavedTeam] = useState<SavedTeam | null>(null);

  function handleUpdateMember(i: number, updater: (m: TeamMember) => TeamMember) {
    setTeam((prev) => prev.map((m, idx) => (idx === i && m !== null) ? updater(m) : m));
  }

  function handlePickPokemon(pokemon: Pokemon) {
    setTeam((prev) =>
      prev.map((m, i) => {
        if (i !== activeSlotIndex) return m;
        if (m === null) return createTeamMember(pokemon);
        return {
          ...m,
          pokemon,
          abilityName: pokemon.abilities[0]?.ability.name ?? "",
          moveNames: [null, null, null, null],
        };
      })
    );
    setPickerOpen(false);
  }

  function handleRemoveSlot(i: number) {
    setTeam((prev) => prev.map((m, idx) => (idx === i ? null : m)));
  }

  function handleClearTeam() {
    setTeam(Array(6).fill(null));
    setActiveSlotIndex(0);
    setActiveSavedTeam(null);
  }

  function handleLoadTeam(loadedTeam: Team, saved: SavedTeam) {
    setTeam(loadedTeam);
    setActiveSlotIndex(0);
    setActiveSavedTeam(saved);
    setLoadPanelOpen(false);
  }

  const filledCount = team.filter(Boolean).length;
  const activeMember = team[activeSlotIndex] ?? null;

  return (
    <div className="max-w-[1400px] mx-auto px-6 py-6 flex flex-col gap-4 min-h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p
            className="text-xs text-text-muted tracking-[0.3em] mb-1"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {'// TEAM BUILDER'}
          </p>
          <div className="flex items-baseline gap-3">
            <h1
              className="text-3xl font-black text-text-primary tracking-tight"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {activeSavedTeam ? activeSavedTeam.name.toUpperCase() : "YOUR TEAM"}
            </h1>
            <span className="text-text-secondary text-sm">{filledCount}/6 Pokémon</span>
          </div>
          {activeSavedTeam && (
            <p className="text-[10px] text-text-muted mt-0.5" style={{ fontFamily: "var(--font-jetbrains)" }}>
              Loaded from saved teams
            </p>
          )}
        </div>

        {/* Save / Load controls */}
        <div className="flex items-center gap-2 shrink-0 pt-1">
          {user ? (
            <>
              <button
                onClick={() => { setLoadPanelOpen((v) => !v); setSaveModalOpen(false); }}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                  loadPanelOpen
                    ? "border-accent/40 bg-accent/10 text-accent"
                    : "border-bg-border bg-bg-elevated text-text-secondary hover:border-accent/30 hover:text-text-primary"
                }`}
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                <FolderOpen size={13} />
                LOAD
                <ChevronDown size={11} className={loadPanelOpen ? "rotate-180 transition-transform" : "transition-transform"} />
              </button>
              <button
                onClick={() => { setSaveModalOpen(true); setLoadPanelOpen(false); }}
                disabled={filledCount === 0}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-accent/30 bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                <Save size={13} />
                {activeSavedTeam ? "UPDATE" : "SAVE"}
              </button>
            </>
          ) : (
            <Link
              href="/auth"
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-bg-border bg-bg-elevated text-text-muted hover:border-accent/30 hover:text-text-primary text-xs transition-all"
              style={{ fontFamily: "var(--font-dm-sans)" }}
            >
              <LogIn size={13} />
              Sign in to save teams
            </Link>
          )}
        </div>
      </div>

      {/* Load panel — inline dropdown */}
      {loadPanelOpen && user && (
        <div className="bg-bg-surface border border-bg-border rounded-2xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3
              className="text-[9px] font-bold text-text-muted tracking-widest"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              SAVED TEAMS
            </h3>
            <button onClick={() => setLoadPanelOpen(false)} className="text-text-muted hover:text-text-primary transition-colors">
              <X size={14} />
            </button>
          </div>
          <LoadTeamsPanel onLoad={handleLoadTeam} />
        </div>
      )}

      {/* Slot strip */}
      <TeamSlotStrip
        team={team}
        activeIndex={activeSlotIndex}
        onSelectSlot={(i) => {
          setActiveSlotIndex(i);
          if (!team[i]) setPickerOpen(true);
        }}
        onOpenPicker={() => setPickerOpen(true)}
        onRemoveSlot={handleRemoveSlot}
        onClear={handleClearTeam}
      />

      {/* Main two-column area */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 flex-1 min-h-0">
        {/* Editor — left */}
        <div className="lg:col-span-3">
          <MemberEditor
            member={activeMember}
            slotIndex={activeSlotIndex}
            onOpenPicker={() => setPickerOpen(true)}
            onUpdate={(updater) => handleUpdateMember(activeSlotIndex, updater)}
          />
        </div>

        {/* Analysis — right */}
        <div className="lg:col-span-2">
          <TeamAnalysisPanel team={team} />
        </div>
      </div>

      {/* Pokémon picker modal */}
      {pickerOpen && (
        <PokemonPickerModal
          onSelect={handlePickPokemon}
          onClose={() => setPickerOpen(false)}
          currentTeam={team}
        />
      )}

      {/* Save modal */}
      {saveModalOpen && (
        <SaveTeamModal
          team={team}
          existingTeam={activeSavedTeam}
          onClose={() => setSaveModalOpen(false)}
          onSaved={(saved) => setActiveSavedTeam(saved)}
        />
      )}
    </div>
  );
}
