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
      ? "#4ade80" // green
      : pct > 25
        ? "#facc15" // yellow
        : "#f87171"; // red

  const glow = pct <= 25 && pct > 0 ? `0 0 8px ${color}60` : "none";

  return (
    <div className="w-full">
      <div
        className={`relative w-full rounded-full overflow-hidden ${
          size === "sm" ? "h-1.5" : "h-2"
        }`}
        style={{
          backgroundColor: "var(--bg-elevated)",
          border: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        {/* Ghost bar — drains slowly behind the real bar for damage feedback */}
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{
            width: `${pct}%`,
            backgroundColor: "rgba(255,255,255,0.12)",
            transition: "width 1s ease-in 0.2s",
          }}
        />
        {/* Real HP bar */}
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{
            width: `${pct}%`,
            backgroundColor: color,
            boxShadow: glow,
            transition:
              "width 0.35s ease-out, background-color 0.3s, box-shadow 0.3s",
          }}
        />
      </div>
      {size === "md" && (
        <div className="flex items-center justify-between mt-1">
          <span
            className="text-[9px] tabular-nums"
            style={{ fontFamily: "var(--font-jetbrains)", color }}
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
