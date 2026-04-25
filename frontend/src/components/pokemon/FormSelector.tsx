"use client";
import { useEffect, useRef } from "react";
import type { PokemonVariety } from "@/src/lib/pokeapi";

interface FormSelectorProps {
  varieties: PokemonVariety[];
  activeFormSuffix: string | null; // null = default form
  onSelect: (suffix: string | null) => void;
}

export function FormSelector({ varieties, activeFormSuffix, onSelect }: FormSelectorProps) {
  const activeRef = useRef<HTMLButtonElement>(null);

  // Scroll active pill into view when it changes
  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: "smooth", inline: "nearest", block: "nearest" });
  }, [activeFormSuffix]);

  if (!varieties || varieties.length <= 1) return null;

  return (
    <div className="relative">
      <div className="flex gap-1.5 overflow-x-auto scrollbar-none px-1 pb-0.5">
        {varieties.map((v) => {
          const isActive = activeFormSuffix === v.formSuffix || (activeFormSuffix === null && v.isDefault);
          return (
            <button
              key={v.formName}
              ref={isActive ? activeRef : undefined}
              onClick={() => onSelect(v.isDefault ? null : v.formSuffix)}
              className={`
                shrink-0 px-2.5 py-1 rounded-md border text-[10px] tracking-wider transition-all
                ${isActive
                  ? "border-accent/50 bg-accent/10 text-accent"
                  : "border-bg-border text-text-secondary hover:border-accent/20 hover:text-text-primary"
                }
              `}
              style={{ fontFamily: "var(--font-jetbrains)" }}
            >
              {v.displayName}
            </button>
          );
        })}
      </div>
    </div>
  );
}
