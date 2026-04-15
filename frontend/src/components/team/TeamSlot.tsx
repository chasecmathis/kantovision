"use client";
import Image from "next/image";
import { X, Plus } from "lucide-react";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { formatPokemonName, getOfficialArtwork, type Pokemon } from "@/src/lib/pokeapi";
import { getTypeGradient } from "@/src/lib/typeColors";
import { padId } from "@/src/lib/utils";

interface TeamSlotProps {
  slot: number;
  pokemon: Pokemon | null;
  onRemove: (slot: number) => void;
  onSelect: (slot: number) => void;
}

export function TeamSlot({ slot, pokemon, onRemove, onSelect }: TeamSlotProps) {
  if (!pokemon) {
    return (
      <button
        onClick={() => onSelect(slot)}
        className="flex flex-col items-center justify-center gap-2 w-full h-32 rounded-xl border-2 border-dashed border-bg-border hover:border-accent/40 hover:bg-accent/5 transition-all group"
      >
        <div className="w-8 h-8 rounded-full border border-bg-border flex items-center justify-center group-hover:border-accent/40 transition-colors">
          <Plus size={14} className="text-text-muted group-hover:text-accent" />
        </div>
        <span
          className="text-text-muted text-[10px] tracking-widest"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          SLOT {slot + 1}
        </span>
      </button>
    );
  }

  const types = pokemon.types.map((t) => t.type.name);
  const gradient = getTypeGradient(types);

  return (
    <div
      className="relative rounded-xl border border-bg-border overflow-hidden group"
      style={{ background: "linear-gradient(135deg, #0e0e1a, #0e0e1a)" }}
    >
      <div className="absolute inset-0 opacity-30" style={{ background: gradient }} />

      <div className="relative p-3 flex flex-col items-center gap-2">
        <button
          onClick={() => onRemove(slot)}
          className="absolute top-2 right-2 w-5 h-5 rounded-full bg-bg-elevated border border-bg-border flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:border-red-500/40 hover:text-red-400 text-text-muted"
        >
          <X size={10} />
        </button>

        <span className="poke-id self-start">#{padId(pokemon.id)}</span>

        <div className="relative w-16 h-16">
          <Image
            src={getOfficialArtwork(pokemon.id)}
            alt={pokemon.name}
            fill
            className="object-contain drop-shadow-md"
            sizes="64px"
            unoptimized
          />
        </div>

        <p
          className="text-xs font-bold text-text-primary text-center leading-tight"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          {formatPokemonName(pokemon.name)}
        </p>

        <div className="flex gap-1 flex-wrap justify-center">
          {types.map((t) => (
            <TypeBadge key={t} type={t} size="sm" />
          ))}
        </div>
      </div>
    </div>
  );
}
