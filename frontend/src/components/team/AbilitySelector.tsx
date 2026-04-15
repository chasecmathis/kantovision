"use client";
import { useState } from "react";
import { useAbility } from "@/src/hooks/usePokemon";
import { formatPokemonName, getEnglishAbilityEffect, type PokemonAbility } from "@/src/lib/pokeapi";

interface AbilitySelectorProps {
  abilities: PokemonAbility[];
  selected: string;
  onChange: (name: string) => void;
}

function AbilityTooltip({ name }: { name: string }) {
  const { data, isLoading } = useAbility(name);
  const effect = data ? getEnglishAbilityEffect(data) : null;

  if (isLoading) return (
    <div className="h-3 w-48 rounded shimmer mt-2" />
  );
  if (!effect) return null;
  return (
    <p className="text-[10px] text-text-secondary mt-2 leading-relaxed border-l-2 border-accent/30 pl-2 animate-fade-in">
      {effect}
    </p>
  );
}

export function AbilitySelector({ abilities, selected, onChange }: AbilitySelectorProps) {
  const [hovered, setHovered] = useState<string | null>(null);
  const activeTooltip = hovered ?? (abilities.length > 0 ? selected : null);

  return (
    <div>
      <div className="flex flex-wrap gap-1.5">
        {abilities.map((a) => {
          const isSelected = a.ability.name === selected;
          return (
            <button
              key={a.ability.name}
              onClick={() => onChange(a.ability.name)}
              onMouseEnter={() => setHovered(a.ability.name)}
              onMouseLeave={() => setHovered(null)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                isSelected
                  ? "border-accent/50 bg-accent/15 text-text-primary"
                  : "border-bg-border bg-bg-elevated text-text-secondary hover:border-accent/25 hover:text-text-primary"
              }`}
              style={{ fontFamily: "var(--font-dm-sans)" }}
            >
              {formatPokemonName(a.ability.name)}
              {a.is_hidden && (
                <span
                  className="text-[9px] text-text-muted"
                  style={{ fontFamily: "var(--font-jetbrains)" }}
                >
                  H
                </span>
              )}
            </button>
          );
        })}
      </div>
      {activeTooltip && <AbilityTooltip name={activeTooltip} />}
    </div>
  );
}
