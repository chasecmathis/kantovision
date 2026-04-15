"use client";

interface HPBarProps {
  current: number;
  max: number;
  size?: "sm" | "md";
}

export function HPBar({ current, max, size = "md" }: HPBarProps) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (current / max) * 100)) : 0;

  const color =
    pct > 50
      ? "#4ade80"   // green
      : pct > 25
      ? "#facc15"   // yellow
      : "#f87171";  // red

  const glow = pct <= 25 ? `0 0 8px ${color}80` : "none";

  return (
    <div className="w-full">
      <div
        className={`w-full rounded-full bg-bg-elevated overflow-hidden ${size === "sm" ? "h-1.5" : "h-2"}`}
        style={{ border: "1px solid rgba(255,255,255,0.06)" }}
      >
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color, boxShadow: glow }}
        />
      </div>
      {size === "md" && (
        <div className="flex items-center justify-between mt-1">
          <span
            className="text-[9px] tabular-nums"
            style={{ fontFamily: "var(--font-jetbrains)", color: color }}
          >
            {current}/{max}
          </span>
          <span
            className="text-[9px] tabular-nums text-text-muted"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {Math.round(pct)}%
          </span>
        </div>
      )}
    </div>
  );
}
