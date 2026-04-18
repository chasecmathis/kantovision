"use client";
import { useEffect, useState } from "react";

interface MoveTimerProps {
  totalSeconds: number;
  active: boolean;
}

const SIZE = 46;
const STROKE = 3.5;
const RADIUS = (SIZE - STROKE * 2) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function ringColor(fraction: number): string {
  if (fraction > 0.4) return "#6c63ff";
  if (fraction > 0.15) return "#eab308";
  return "#ef4444";
}

export function MoveTimer({ totalSeconds, active }: MoveTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState(totalSeconds);

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => {
      setSecondsLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [active]);

  const fraction = secondsLeft / totalSeconds;
  const dashOffset = CIRCUMFERENCE * (1 - fraction);
  const color = active ? ringColor(fraction) : "#1c1c30";
  const isUrgent = secondsLeft <= 10 && active && secondsLeft > 0;

  return (
    <div
      className="relative flex items-center justify-center shrink-0"
      style={{
        width: SIZE,
        height: SIZE,
        animation: isUrgent ? "pulseGlow 0.8s ease-in-out infinite" : undefined,
        filter: isUrgent ? `drop-shadow(0 0 4px ${color}80)` : undefined,
      }}
    >
      <svg
        width={SIZE}
        height={SIZE}
        style={{ transform: "rotate(-90deg)", overflow: "visible" }}
      >
        {/* Track */}
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="#1c1c30"
          strokeWidth={STROKE}
        />
        {/* Progress arc */}
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          style={{
            transition: "stroke-dashoffset 0.85s linear, stroke 0.4s ease",
          }}
        />
      </svg>

      {/* Countdown number */}
      <span
        className="absolute tabular-nums leading-none font-bold"
        style={{
          fontFamily: "var(--font-jetbrains)",
          fontSize: secondsLeft >= 10 ? 12 : 13,
          color: active ? color : "#4a4870",
          transition: "color 0.4s ease",
          letterSpacing: "-0.02em",
        }}
      >
        {secondsLeft}
      </span>
    </div>
  );
}
