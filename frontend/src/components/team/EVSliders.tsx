"use client";
import { STAT_DISPLAY, STAT_ORDER, totalEVs, type EVSpread } from "@/src/lib/pokeapi";

interface EVSlidersProps {
  evs: EVSpread;
  onChange: (evs: EVSpread) => void;
}

const STAT_COLORS: Record<string, string> = {
  hp: "#4ADE80",
  attack: "#F97316",
  defense: "#60A5FA",
  "special-attack": "#C084FC",
  "special-defense": "#818CF8",
  speed: "#FBBF24",
};

export function EVSliders({ evs, onChange }: EVSlidersProps) {
  const used = totalEVs(evs);
  const remaining = 510 - used;

  function handleChange(stat: string, raw: number) {
    const step4 = Math.round(raw / 4) * 4;
    const clamped = Math.min(252, Math.max(0, step4));
    // Can't exceed remaining budget (accounting for current value)
    const maxAllowed = Math.min(252, clamped, (evs[stat as keyof EVSpread]) + remaining);
    const final = Math.min(clamped, maxAllowed);
    onChange({ ...evs, [stat]: final });
  }

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] text-text-muted tracking-widest" style={{ fontFamily: "var(--font-unbounded)" }}>
          EV REMAINING
        </span>
        <span
          className={`text-xs font-bold tabular-nums ${remaining === 0 ? "text-orange-400" : remaining < 100 ? "text-yellow-400" : "text-green-400"}`}
          style={{ fontFamily: "var(--font-jetbrains)" }}
        >
          {remaining} / 510
        </span>
      </div>

      {STAT_ORDER.map((stat) => {
        const value = evs[stat];
        const pct = (value / 252) * 100;
        const color = STAT_COLORS[stat] ?? "#6c63ff";
        const maxAllowed = Math.min(252, value + remaining);

        return (
          <div key={stat} className="flex items-center gap-2">
            <span
              className="w-12 text-right text-[9px] font-bold text-text-secondary shrink-0"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {STAT_DISPLAY[stat]}
            </span>

            {/* Custom slider */}
            <div className="flex-1 relative h-5 flex items-center">
              {/* Track */}
              <div className="absolute inset-0 flex items-center">
                <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-100"
                    style={{ width: `${pct}%`, backgroundColor: color, boxShadow: value > 0 ? `0 0 6px ${color}50` : "none" }}
                  />
                </div>
              </div>
              {/* Native range (transparent overlay) */}
              <input
                type="range"
                min={0}
                max={maxAllowed}
                step={4}
                value={value}
                onChange={(e) => handleChange(stat, parseInt(e.target.value, 10))}
                className="absolute inset-0 w-full opacity-0 cursor-pointer h-5"
                style={{ zIndex: 1 }}
              />
            </div>

            <span
              className="w-8 text-right text-xs tabular-nums text-text-primary shrink-0"
              style={{ fontFamily: "var(--font-jetbrains)", color: value > 0 ? color : undefined }}
            >
              {value}
            </span>
          </div>
        );
      })}
    </div>
  );
}
