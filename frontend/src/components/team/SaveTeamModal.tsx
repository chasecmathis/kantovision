"use client";
import { useState } from "react";
import { X, Save, AlertCircle } from "lucide-react";
import { useCreateTeam, useUpdateTeam } from "@/src/hooks/useTeams";
import type { Team } from "@/src/lib/pokeapi";
import type { SavedTeam } from "@/src/lib/api";

interface SaveTeamModalProps {
  team: Team;
  existingTeam?: SavedTeam | null; // if set, we're overwriting
  onClose: () => void;
  onSaved: (saved: SavedTeam) => void;
}

export function SaveTeamModal({ team, existingTeam, onClose, onSaved }: SaveTeamModalProps) {
  const [name, setName] = useState(existingTeam?.name ?? "");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useCreateTeam();
  const updateMutation = useUpdateTeam();
  const isPending = createMutation.isPending || updateMutation.isPending;

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmed = name.trim();
    if (!trimmed) { setError("Please enter a team name."); return; }
    try {
      let saved: SavedTeam;
      if (existingTeam) {
        saved = await updateMutation.mutateAsync({ id: existingTeam.id, name: trimmed, team });
      } else {
        saved = await createMutation.mutateAsync({ name: trimmed, team });
      }
      onSaved(saved);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save team.");
    }
  }

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-sm bg-bg-surface border border-bg-border rounded-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-bg-border">
          <h2
            className="text-sm font-bold text-text-primary tracking-widest"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            {existingTeam ? "UPDATE TEAM" : "SAVE TEAM"}
          </h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-5 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
              <AlertCircle size={13} className="shrink-0" />
              <p className="text-[11px]" style={{ fontFamily: "var(--font-jetbrains)" }}>{error}</p>
            </div>
          )}

          <div className="space-y-1.5">
            <label
              className="block text-[9px] tracking-widest text-text-muted"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              TEAM NAME
            </label>
            <input
              autoFocus
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Rain Offense, Sun Team..."
              maxLength={40}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={isPending}
            className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs tracking-widest py-2.5 rounded-lg transition-all"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            {isPending ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Save size={13} />
                {existingTeam ? "UPDATE" : "SAVE"}
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
