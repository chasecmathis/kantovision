"use client";
import Image from "next/image";
import { Plus, X } from "lucide-react";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { formatPokemonName, getFrontDefault, getOfficialArtwork, type Team } from "@/src/lib/pokeapi";
import { getTypeGradient } from "@/src/lib/typeColors";

interface TeamSlotStripProps {
  team: Team;
  activeIndex: number;
  onSelectSlot: (i: number) => void;
  onOpenPicker: () => void;
  onRemoveSlot: (i: number) => void;
  onClear: () => void;
}

export function TeamSlotStrip({
  team,
  activeIndex,
  onSelectSlot,
  onOpenPicker,
  onRemoveSlot,
  onClear,
}: TeamSlotStripProps) {
  const filledCount = team.filter(Boolean).length;

  return (
    <div className="flex items-stretch gap-2">
      {team.map((member, i) => {
        const isActive = i === activeIndex;
        const pokemon = member?.pokemon ?? null;
        const types = pokemon?.types.map((t) => t.type.name) ?? [];
        const gradient = types.length > 0 ? getTypeGradient(types) : undefined;

        if (!pokemon) {
          return (
            <button
              key={i}
              onClick={() => { onSelectSlot(i); onOpenPicker(); }}
              className={`flex-1 min-w-0 flex flex-col items-center justify-center gap-1 py-3 rounded-xl border-2 border-dashed transition-all ${
                isActive
                  ? "border-accent/50 bg-accent/5"
                  : "border-bg-border hover:border-accent/25 hover:bg-accent/3"
              }`}
            >
              <Plus size={14} className={isActive ? "text-accent" : "text-text-muted"} />
              <span
                className="text-[9px] text-text-muted tracking-widest"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                {i + 1}
              </span>
            </button>
          );
        }

        return (
          <button
            key={i}
            onClick={() => onSelectSlot(i)}
            className={`relative flex-1 min-w-0 flex items-center gap-2 px-3 py-2 rounded-xl border-2 transition-all overflow-hidden group ${
              isActive
                ? "border-accent/60 bg-bg-elevated"
                : "border-bg-border bg-bg-surface hover:border-accent/25"
            }`}
          >
            {gradient && (
              <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ background: gradient }} />
            )}

            {/* Remove button */}
            <button
              onClick={(e) => { e.stopPropagation(); onRemoveSlot(i); }}
              className="absolute top-1 right-1 w-4 h-4 rounded-full bg-bg-elevated border border-bg-border flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:border-red-500/40 hover:text-red-400 text-text-muted z-10"
            >
              <X size={8} />
            </button>

            <div className="relative w-9 h-9 shrink-0">
              <Image
                src={getFrontDefault(pokemon.id)}
                alt={pokemon.name}
                fill
                className="object-contain drop-shadow"
                sizes="36px"
                unoptimized
              />
            </div>
            <div className="flex flex-col items-start gap-0.5 min-w-0 relative">
              <span
                className="text-[9px] font-bold text-text-primary leading-tight truncate w-full"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                {formatPokemonName(pokemon.name)}
              </span>
              <div className="flex gap-0.5">
                {types.map((t) => (
                  <TypeBadge key={t} type={t} size="sm" />
                ))}
              </div>
            </div>
          </button>
        );
      })}

      {filledCount > 0 && (
        <button
          onClick={onClear}
          className="shrink-0 px-3 py-2 rounded-xl border border-bg-border text-[9px] text-text-muted hover:border-red-500/30 hover:text-red-400 transition-all self-stretch flex items-center"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          CLR
        </button>
      )}
    </div>
  );
}
