"use client";
import type { PokemonVariety } from "@/src/lib/pokeapi";

interface FormSwitcherProps {
  varieties: PokemonVariety[];
  currentFormName: string | null; // full form name like "graveler-alola", or null for default
  isLoading: boolean;
  onSwitch: (formName: string | null) => void;
}

export function FormSwitcher({ varieties, currentFormName, isLoading, onSwitch }: FormSwitcherProps) {
  if (!varieties || varieties.length <= 1) return null;

  return (
    <div className="flex gap-1 flex-wrap">
      {varieties.map((v) => {
        const isActive =
          currentFormName === v.formName ||
          (currentFormName === null && v.isDefault);
        return (
          <button
            key={v.formName}
            disabled={isLoading}
            onClick={() => onSwitch(v.isDefault ? null : v.formName)}
            className={`
              relative px-2 py-0.5 rounded border text-[9px] tracking-wider transition-all
              disabled:opacity-60 disabled:cursor-not-allowed
              ${isActive
                ? "border-accent/50 bg-accent/10 text-accent"
                : "border-bg-border text-text-secondary hover:border-accent/20 hover:text-text-primary"
              }
            `}
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {/* Loading shimmer on the active pill */}
            {isActive && isLoading && (
              <span className="absolute inset-0 rounded border border-accent/30 animate-pulse bg-accent/5" />
            )}
            {v.displayName}
          </button>
        );
      })}
    </div>
  );
}
