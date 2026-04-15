"use client";
import { useEffect, useRef, useState } from "react";
import { formatStatName } from "@/src/lib/pokeapi";
import { cn } from "@/src/lib/utils";

interface StatBarProps {
  name: string;
  value: number;
  max?: number;
  color?: string;
  delay?: number;
}

export function StatBar({ name, value, max = 255, color = "#6c63ff", delay = 0 }: StatBarProps) {
  const [filled, setFilled] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setFilled(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const pct = Math.round((value / max) * 100);
  const displayColor =
    value >= 100 ? "#4ADE80" :
    value >= 70 ? "#FBBF24" :
    value >= 40 ? "#F97316" : "#EF4444";

  return (
    <div className="flex items-center gap-3 group">
      <span
        className="w-16 text-right text-[10px] font-medium tracking-wider text-text-secondary shrink-0"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {formatStatName(name)}
      </span>
      <span
        className="w-8 text-right text-sm font-mono text-text-primary shrink-0"
        style={{ fontFamily: "var(--font-jetbrains)" }}
      >
        {value}
      </span>
      <div className="flex-1 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
        <div
          ref={ref}
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: filled ? `${pct}%` : "0%",
            backgroundColor: displayColor,
            boxShadow: filled ? `0 0 8px ${displayColor}60` : "none",
            transitionDelay: `${delay}ms`,
          }}
        />
      </div>
      <span
        className="w-6 text-[10px] text-text-muted shrink-0"
        style={{ fontFamily: "var(--font-jetbrains)" }}
      >
        {pct}%
      </span>
    </div>
  );
}
