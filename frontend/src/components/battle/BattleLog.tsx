"use client";
import { useEffect, useRef } from "react";

interface BattleLogProps {
  entries: string[];
}

export function BattleLog({ entries }: BattleLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  return (
    <div
      className="rounded-xl border border-bg-border bg-bg-surface overflow-hidden flex flex-col"
      style={{ minHeight: 120, maxHeight: 180 }}
    >
      <div
        className="px-3 py-1.5 border-b border-bg-border"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        <span className="text-[8px] font-bold text-text-muted tracking-[0.25em]">BATTLE LOG</span>
      </div>
      <div className="overflow-y-auto flex-1 p-2 space-y-0.5">
        {entries.length === 0 ? (
          <p className="text-[10px] text-text-muted px-1" style={{ fontFamily: "var(--font-dm-sans)" }}>
            Waiting for battle to start...
          </p>
        ) : (
          entries.map((entry, i) => (
            <p
              key={i}
              className="text-[10px] text-text-secondary leading-relaxed animate-in fade-in duration-300"
              style={{ fontFamily: "var(--font-jetbrains)" }}
            >
              <span className="text-text-muted select-none mr-1.5" style={{ fontSize: 8 }}>›</span>
              {entry}
            </p>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
