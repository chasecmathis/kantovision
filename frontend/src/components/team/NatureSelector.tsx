"use client";
import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useNatureList } from "@/src/hooks/usePokemon";
import { formatPokemonName, STAT_DISPLAY, type Nature } from "@/src/lib/pokeapi";

interface NatureSelectorProps {
  selected: string | null;
  onChange: (name: string | null) => void;
}

function NatureCell({ nature, selected, onSelect }: { nature: Nature; selected: boolean; onSelect: () => void }) {
  const boosted = nature.increased_stat?.name ?? null;
  const reduced = nature.decreased_stat?.name ?? null;
  const isNeutral = !boosted && !reduced;

  return (
    <button
      onClick={onSelect}
      className={`flex flex-col items-center gap-0.5 p-1.5 rounded-lg border transition-all text-center ${
        selected
          ? "border-accent/50 bg-accent/10"
          : "border-bg-border bg-bg-elevated hover:border-accent/25 hover:bg-bg-elevated"
      }`}
    >
      <span
        className="text-[9px] font-bold text-text-primary leading-tight"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {nature.name.charAt(0).toUpperCase() + nature.name.slice(1)}
      </span>
      {isNeutral ? (
        <span className="text-[8px] text-text-muted" style={{ fontFamily: "var(--font-jetbrains)" }}>—</span>
      ) : (
        <div className="flex flex-col items-center gap-0.5">
          {boosted && (
            <span className="text-[8px] text-green-400 leading-none" style={{ fontFamily: "var(--font-jetbrains)" }}>
              +{STAT_DISPLAY[boosted] ?? boosted}
            </span>
          )}
          {reduced && (
            <span className="text-[8px] text-red-400 leading-none" style={{ fontFamily: "var(--font-jetbrains)" }}>
              -{STAT_DISPLAY[reduced] ?? reduced}
            </span>
          )}
        </div>
      )}
    </button>
  );
}

export function NatureSelector({ selected, onChange }: NatureSelectorProps) {
  const [expanded, setExpanded] = useState(false);
  const { data: natures, isLoading } = useNatureList();

  const selectedNature = natures?.find((n) => n.name === selected);
  const boosted = selectedNature?.increased_stat?.name;
  const reduced = selectedNature?.decreased_stat?.name;

  return (
    <div>
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center justify-between w-full group"
      >
        <div className="flex items-center gap-2">
          {selected ? (
            <span className="text-xs text-text-primary font-medium" style={{ fontFamily: "var(--font-dm-sans)" }}>
              {selected.charAt(0).toUpperCase() + selected.slice(1)}
            </span>
          ) : (
            <span className="text-xs text-text-muted">None selected</span>
          )}
          {selected && boosted && (
            <span className="text-[10px] text-green-400" style={{ fontFamily: "var(--font-jetbrains)" }}>
              +{STAT_DISPLAY[boosted]}
            </span>
          )}
          {selected && reduced && (
            <span className="text-[10px] text-red-400" style={{ fontFamily: "var(--font-jetbrains)" }}>
              -{STAT_DISPLAY[reduced]}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp size={13} className="text-text-muted" />
        ) : (
          <ChevronDown size={13} className="text-text-muted" />
        )}
      </button>

      {expanded && (
        <div className="mt-3 animate-fade-in">
          {isLoading ? (
            <div className="grid grid-cols-5 gap-1">
              {Array.from({ length: 25 }).map((_, i) => (
                <div key={i} className="h-12 rounded-lg shimmer" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-5 gap-1">
              {(natures ?? [])
                .slice()
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((nature) => (
                  <NatureCell
                    key={nature.name}
                    nature={nature}
                    selected={nature.name === selected}
                    onSelect={() => {
                      onChange(nature.name === selected ? null : nature.name);
                      setExpanded(false);
                    }}
                  />
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
