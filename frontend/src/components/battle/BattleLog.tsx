"use client";
import { useEffect, useRef } from "react";

interface BattleLogProps {
  entries: string[];
}

function getEntryStyle(entry: string): {
  color: string;
  weight?: number;
  opacity?: number;
} {
  const lower = entry.toLowerCase();

  // KO
  if (lower.includes("fainted")) return { color: "#f87171", weight: 600 };

  // Effectiveness
  if (lower.includes("super effective"))
    return { color: "#4ade80", weight: 500 };
  if (lower.includes("critical hit")) return { color: "#fbbf24", weight: 500 };
  if (lower.includes("not very effective"))
    return { color: "#4a4870", opacity: 0.85 };
  if (lower.includes("had no effect"))
    return { color: "#4a4870", opacity: 0.7 };

  // Switch-in
  if (lower.startsWith("go,") || lower.includes("go,"))
    return { color: "#60a5fa" };

  // Move usage
  if (lower.includes("used")) return { color: "#c8c6e0" };

  // Status conditions
  if (lower.includes("burned") || lower.includes("burn"))
    return { color: "#f97316" };
  if (lower.includes("paralyzed") || lower.includes("paralysis"))
    return { color: "#eab308" };
  if (lower.includes("poisoned") || lower.includes("badly poisoned"))
    return { color: "#a855f7" };
  if (lower.includes("fell asleep") || lower.includes("fast asleep"))
    return { color: "#94a3b8" };
  if (lower.includes("frozen") || lower.includes("freeze"))
    return { color: "#06b6d4" };

  // Recovery / healing
  if (
    lower.includes("restored") ||
    lower.includes("healed") ||
    lower.includes("recovered")
  )
    return { color: "#4ade80", opacity: 0.85 };

  // Residual damage
  if (
    lower.includes("hurt by") ||
    lower.includes("buffeted") ||
    lower.includes("damaged")
  )
    return { color: "#d97706" };

  // Stat changes
  if (lower.includes("rose") || lower.includes("raised"))
    return { color: "#4ade80", opacity: 0.8 };
  if (
    lower.includes("fell") ||
    lower.includes("lowered") ||
    lower.includes("won't go")
  )
    return { color: "#f87171", opacity: 0.8 };

  // Protect / blocked
  if (lower.includes("protected") || lower.includes("failed"))
    return { color: "#94a3b8" };

  return { color: "var(--text-secondary)" };
}

export function BattleLog({ entries }: BattleLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  return (
    <div
      className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden flex flex-col"
      style={{ minHeight: 140, maxHeight: 240 }}
    >
      {/* Header */}
      <div className="px-3 py-1.5 border-b border-bg-border flex items-center gap-2">
        <div
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ backgroundColor: "#6c63ff" }}
        />
        <span
          className="text-[8px] font-bold text-text-muted tracking-[0.25em]"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          BATTLE LOG
        </span>
        {entries.length > 0 && (
          <span
            className="text-[8px] tabular-nums text-text-muted ml-auto"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {entries.length}
          </span>
        )}
      </div>

      {/* Entries */}
      <div className="overflow-y-auto flex-1 p-1.5 space-y-px">
        {entries.length === 0 ? (
          <p
            className="text-[10px] text-text-muted px-1.5 py-2"
            style={{ fontFamily: "var(--font-dm-sans)" }}
          >
            Waiting for battle to start...
          </p>
        ) : (
          entries.map((entry, i) => {
            const style = getEntryStyle(entry);
            const isRecent = i >= entries.length - 6;
            return (
              <p
                key={i}
                className="text-[10px] leading-relaxed px-1.5 py-0.5 rounded transition-colors hover:bg-white/[0.02]"
                style={{
                  fontFamily: "var(--font-jetbrains)",
                  color: style.color,
                  fontWeight: style.weight ?? 400,
                  opacity: style.opacity ?? 1,
                  animation: isRecent
                    ? "fadeIn 0.3s ease forwards"
                    : undefined,
                }}
              >
                <span
                  className="select-none mr-1 inline-block"
                  style={{
                    fontSize: 7,
                    color: "var(--text-muted)",
                    opacity: 0.4,
                  }}
                >
                  {"\u203a"}
                </span>
                {entry}
              </p>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
