"use client";
import Link from "next/link";
import Image from "next/image";
import { TypeBadge } from "./TypeBadge";
import { padId } from "@/src/lib/utils";
import { getOfficialArtwork, formatPokemonName, type Pokemon } from "@/src/lib/pokeapi";
import { getTypeGradient } from "@/src/lib/typeColors";

interface PokemonCardProps {
  pokemon: Pokemon;
  index?: number;
  onClick?: (pokemon: Pokemon) => void;
  selected?: boolean;
  compact?: boolean;
  formCount?: number;
}

export function PokemonCard({
  pokemon,
  index = 0,
  onClick,
  selected,
  compact,
  formCount,
}: PokemonCardProps) {
  const types = pokemon.types.map((t) => t.type.name);
  const gradient = getTypeGradient(types);
  const artwork = getOfficialArtwork(pokemon.id);

  const content = (
    <div
      className={`
        relative rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden
        ${selected
          ? "border-accent/60 bg-accent/10 shadow-lg shadow-accent/10"
          : "border-bg-border bg-bg-surface hover:border-accent/30 hover:bg-bg-elevated"
        }
        ${compact ? "p-3" : "p-4"}
      `}
      style={{ background: `linear-gradient(135deg, #0e0e1a, #0e0e1a), ${gradient}` }}
      onClick={() => onClick?.(pokemon)}
    >
      {/* Gradient overlay */}
      <div
        className="absolute inset-0 opacity-50 pointer-events-none"
        style={{ background: gradient }}
      />

      {/* ID */}
      <span className="poke-id absolute top-3 right-3">#{padId(pokemon.id)}</span>

      {/* Sprite */}
      <div className={`relative mx-auto ${compact ? "w-16 h-16" : "w-24 h-24"}`}>
        <Image
          src={artwork}
          alt={pokemon.name}
          fill
          className="object-contain drop-shadow-lg transition-transform duration-200 hover:scale-105"
          sizes={compact ? "64px" : "96px"}
          unoptimized
        />
      </div>

      {/* Name */}
      <p
        className={`mt-2 font-bold text-text-primary text-center leading-tight ${compact ? "text-xs" : "text-sm"}`}
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {formatPokemonName(pokemon.name)}
      </p>

      {/* Types */}
      <div className="flex justify-center gap-1 mt-2 flex-wrap">
        {types.map((t) => (
          <TypeBadge key={t} type={t} size="sm" />
        ))}
      </div>
    </div>
  );

  if (onClick) return content;

  return (
    <Link
      href={`/pokedex/${pokemon.id}`}
      className="block animate-fade-up"
      style={{ animationDelay: `${Math.min(index * 30, 500)}ms`, animationFillMode: "both" }}
    >
      {content}
    </Link>
  );
}

export function PokemonCardSkeleton() {
  return (
    <div className="rounded-xl border border-bg-border bg-bg-surface p-4 animate-pulse">
      <div className="w-24 h-24 mx-auto rounded-full shimmer" />
      <div className="mt-3 h-3 w-20 mx-auto rounded shimmer" />
      <div className="mt-2 flex justify-center gap-1">
        <div className="h-5 w-12 rounded shimmer" />
      </div>
    </div>
  );
}
