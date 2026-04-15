"use client";
import { STAT_DISPLAY, STAT_ORDER, type IVSpread } from "@/src/lib/pokeapi";

interface IVInputsProps {
  ivs: IVSpread;
  onChange: (ivs: IVSpread) => void;
}

const STAT_COLORS: Record<string, string> = {
  hp: "#4ADE80",
  attack: "#F97316",
  defense: "#60A5FA",
  "special-attack": "#C084FC",
  "special-defense": "#818CF8",
  speed: "#FBBF24",
};

export function IVInputs({ ivs, onChange }: IVInputsProps) {
  function set(stat: string, value: number) {
    onChange({ ...ivs, [stat]: Math.min(31, Math.max(0, value)) });
  }

  return (
    <div className="space-y-1.5">
      {STAT_ORDER.map((stat) => {
        const value = ivs[stat];
        const color = STAT_COLORS[stat] ?? "#6c63ff";
        const isPerfect = value === 31;

        return (
          <div key={stat} className="flex items-center gap-2">
            {/* Stat label */}
            <span
              className="w-12 text-right text-[9px] font-bold text-text-secondary shrink-0"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {STAT_DISPLAY[stat]}
            </span>

            {/* Track */}
            <div className="flex-1 relative h-1.5 bg-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-100"
                style={{
                  width: `${(value / 31) * 100}%`,
                  backgroundColor: color,
                  boxShadow: value > 0 ? `0 0 6px ${color}50` : "none",
                }}
              />
            </div>

            {/* Stepper control: [−] [value] [+] */}
            <div
              className="flex items-center shrink-0 rounded-lg overflow-hidden border border-bg-border bg-bg-elevated"
              style={{ borderColor: isPerfect ? `${color}40` : undefined }}
            >
              <button
                type="button"
                onClick={() => set(stat, value - 1)}
                disabled={value === 0}
                className="w-6 h-6 flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-white/5 disabled:opacity-20 disabled:cursor-not-allowed transition-colors border-r border-bg-border"
                aria-label={`Decrease ${stat}`}
              >
                <span className="text-sm leading-none" style={{ fontFamily: "var(--font-jetbrains)" }}>−</span>
              </button>

              <span
                className="w-7 text-center text-xs tabular-nums leading-none py-1 select-none"
                style={{
                  fontFamily: "var(--font-jetbrains)",
                  color: isPerfect ? color : "var(--text-primary)",
                }}
              >
                {value}
              </span>

              <button
                type="button"
                onClick={() => set(stat, value + 1)}
                disabled={value === 31}
                className="w-6 h-6 flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-white/5 disabled:opacity-20 disabled:cursor-not-allowed transition-colors border-l border-bg-border"
                aria-label={`Increase ${stat}`}
              >
                <span className="text-sm leading-none" style={{ fontFamily: "var(--font-jetbrains)" }}>+</span>
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
