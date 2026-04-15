"use client";
import { useState } from "react";
import { Trash2, Upload, Clock, ChevronRight } from "lucide-react";
import { useSavedTeams, useDeleteTeam, hydrateTeam } from "@/src/hooks/useTeams";
import type { Team } from "@/src/lib/pokeapi";
import type { SavedTeam } from "@/src/lib/api";

interface LoadTeamsPanelProps {
  onLoad: (team: Team, savedTeam: SavedTeam) => void;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function LoadTeamsPanel({ onLoad }: LoadTeamsPanelProps) {
  const { data: teams, isLoading, error } = useSavedTeams();
  const deleteMutation = useDeleteTeam();
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleLoad(saved: SavedTeam) {
    setLoadingId(saved.id);
    try {
      const team = await hydrateTeam(saved.slots);
      // Pad to 6
      while (team.length < 6) team.push(null);
      onLoad(team, saved);
    } finally {
      setLoadingId(null);
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(id);
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-14 rounded-xl shimmer" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-[11px] text-red-400 text-center py-4" style={{ fontFamily: "var(--font-jetbrains)" }}>
        Failed to load teams.
      </p>
    );
  }

  if (!teams || teams.length === 0) {
    return (
      <p className="text-[11px] text-text-muted text-center py-6" style={{ fontFamily: "var(--font-jetbrains)" }}>
        No saved teams yet.
      </p>
    );
  }

  return (
    <div className="space-y-1.5">
      {teams.map((saved) => {
        const filledCount = saved.slots.filter(Boolean).length;
        const isLoading = loadingId === saved.id;
        const isDeleting = deletingId === saved.id;

        return (
          <button
            key={saved.id}
            onClick={() => handleLoad(saved)}
            disabled={isLoading || isDeleting}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border border-bg-border bg-bg-elevated hover:border-accent/30 hover:bg-accent/5 transition-all group disabled:opacity-50 disabled:cursor-not-allowed text-left"
          >
            {/* Load spinner or arrow */}
            <div className="shrink-0 w-5 flex items-center justify-center">
              {isLoading ? (
                <span className="w-4 h-4 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
              ) : (
                <ChevronRight size={14} className="text-text-muted group-hover:text-accent transition-colors" />
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p
                className="text-xs font-bold text-text-primary truncate"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                {saved.name}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-text-muted" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {filledCount}/6 Pokémon
                </span>
                <span className="text-text-muted/40 text-[10px]">·</span>
                <Clock size={9} className="text-text-muted/60" />
                <span className="text-[10px] text-text-muted/60" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {relativeTime(saved.updated_at)}
                </span>
              </div>
            </div>

            {/* Delete */}
            <button
              onClick={(e) => handleDelete(saved.id, e)}
              disabled={isDeleting}
              className="shrink-0 w-7 h-7 rounded-lg border border-transparent hover:border-red-500/30 hover:bg-red-500/10 flex items-center justify-center text-text-muted hover:text-red-400 transition-all opacity-0 group-hover:opacity-100"
            >
              {isDeleting ? (
                <span className="w-3.5 h-3.5 border-2 border-red-400/30 border-t-red-400 rounded-full animate-spin" />
              ) : (
                <Trash2 size={12} />
              )}
            </button>
          </button>
        );
      })}

      <p
        className="text-[10px] text-text-muted text-center pt-1"
        style={{ fontFamily: "var(--font-jetbrains)" }}
      >
        {teams.length}/10 teams saved
      </p>
    </div>
  );
}
