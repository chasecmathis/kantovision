"use client";
import { Shield } from "lucide-react";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { ALL_TYPES, getEffectiveness } from "@/src/lib/typeChart";
import { type Team } from "@/src/lib/pokeapi";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function effToLabel(eff: number | null): string {
  if (eff === null || eff === 1) return "";
  if (eff === 0) return "0";
  if (eff === 0.25) return "¼";
  if (eff === 0.5) return "½";
  if (eff === 2) return "2×";
  if (eff === 4) return "4×";
  return "";
}

function effToColors(eff: number | null): { bg: string; border: string; text: string } {
  if (eff === null) return { bg: "transparent", border: "rgba(255,255,255,0.04)", text: "transparent" };
  if (eff === 0)    return { bg: "rgba(59,130,246,0.15)", border: "rgba(59,130,246,0.35)", text: "#60a5fa" };
  if (eff === 0.25) return { bg: "rgba(34,197,94,0.18)",  border: "rgba(34,197,94,0.4)",  text: "#4ade80" };
  if (eff === 0.5)  return { bg: "rgba(34,197,94,0.10)",  border: "rgba(34,197,94,0.25)", text: "#86efac" };
  if (eff === 1)    return { bg: "transparent",            border: "rgba(255,255,255,0.06)", text: "transparent" };
  if (eff === 2)    return { bg: "rgba(249,115,22,0.15)", border: "rgba(249,115,22,0.35)", text: "#fb923c" };
  if (eff === 4)    return { bg: "rgba(239,68,68,0.20)",  border: "rgba(239,68,68,0.45)",  text: "#f87171" };
  return { bg: "transparent", border: "rgba(255,255,255,0.06)", text: "transparent" };
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function SectionHeader({ label, color, count }: { label: string; color: string; count: number }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span
        className="text-[9px] font-bold tracking-[0.2em]"
        style={{ fontFamily: "var(--font-unbounded)", color }}
      >
        {label}
      </span>
      <div className="flex-1 h-px" style={{ backgroundColor: color + "25" }} />
      <span
        className="text-[9px] tabular-nums"
        style={{ fontFamily: "var(--font-jetbrains)", color: color + "80" }}
      >
        {count}
      </span>
    </div>
  );
}

function WeaknessRow({ type, slots }: { type: string; slots: (number | null)[] }) {
  return (
    <div className="flex items-center gap-2">
      {/* Type badge, fixed width */}
      <div className="w-[72px] shrink-0">
        <TypeBadge type={type} size="sm" />
      </div>

      {/* 6 heat cells — one per team slot */}
      <div className="flex gap-0.5 flex-1">
        {slots.map((eff, i) => {
          const { bg, border, text } = effToColors(eff);
          const label = effToLabel(eff);
          return (
            <div
              key={i}
              className="flex-1 h-[18px] rounded flex items-center justify-center transition-colors"
              style={{ backgroundColor: bg, border: `1px solid ${border}` }}
            >
              {label && (
                <span
                  className="text-[8px] font-bold leading-none"
                  style={{ fontFamily: "var(--font-jetbrains)", color: text }}
                >
                  {label}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

interface TeamAnalysisPanelProps {
  team: Team;
}

export function TeamAnalysisPanel({ team }: TeamAnalysisPanelProps) {
  const slots = team.map((m) => m?.pokemon ?? null);
  const filledCount = slots.filter(Boolean).length;

  if (filledCount === 0) {
    return (
      <div className="h-full min-h-48 flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-bg-border text-text-muted p-6">
        <Shield size={22} strokeWidth={1} />
        <div className="text-center">
          <p className="text-xs font-medium text-text-secondary">Add Pokémon to analyze</p>
          <p className="text-[10px] mt-1">Defensive coverage appears here</p>
        </div>
      </div>
    );
  }

  // Build per-type effectiveness rows across all 6 slots
  const typeData = ALL_TYPES.map((atkType) => {
    const effSlots = slots.map((mon) =>
      mon ? getEffectiveness(atkType, mon.types.map((t) => t.type.name)) : null
    );
    const nonNull = effSlots.filter((e): e is number => e !== null);
    const maxHit = nonNull.length ? Math.max(...nonNull) : 0;
    const weakCount = nonNull.filter((e) => e >= 2).length;
    const resistCount = nonNull.filter((e) => e > 0 && e <= 0.5).length;
    const immuneCount = nonNull.filter((e) => e === 0).length;
    return { type: atkType, effSlots, maxHit, weakCount, resistCount, immuneCount };
  });

  // Weaknesses: at least 1 team member takes ≥2× damage
  const weaknesses = typeData
    .filter((r) => r.weakCount > 0)
    .sort((a, b) => b.maxHit - a.maxHit || b.weakCount - a.weakCount);

  // Resisted: no weaknesses, at least 1 resist or immunity
  const resisted = typeData.filter(
    (r) => r.weakCount === 0 && (r.resistCount > 0 || r.immuneCount > 0)
  );
  const immunities = resisted.filter((r) => r.immuneCount > 0);
  const resistOnly = resisted.filter((r) => r.immuneCount === 0);

  return (
    <div className="bg-bg-surface border border-bg-border rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-bg-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={11} className="text-accent" />
          <span
            className="text-[9px] font-bold text-text-muted tracking-[0.25em]"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            DEFENSIVE COVERAGE
          </span>
        </div>
        {/* Slot labels */}
        <div className="flex gap-0.5">
          {slots.map((mon, i) => (
            <div
              key={i}
              className="w-5 h-3 rounded-sm flex items-center justify-center"
              style={{
                backgroundColor: mon ? "rgba(108,99,255,0.15)" : "transparent",
                border: `1px solid ${mon ? "rgba(108,99,255,0.3)" : "rgba(255,255,255,0.05)"}`,
              }}
            >
              {mon && (
                <span className="text-[6px] text-accent/70" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {i + 1}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="overflow-y-auto max-h-[calc(100vh-280px)]">
        {/* Legend */}
        <div className="px-4 pt-3 pb-2 flex items-center gap-3 flex-wrap border-b border-bg-border/50">
          {[
            { eff: 4, label: "4× weak" },
            { eff: 2, label: "2× weak" },
            { eff: 0.5, label: "½ resist" },
            { eff: 0, label: "immune" },
          ].map(({ eff, label }) => {
            const { bg, border, text } = effToColors(eff);
            return (
              <div key={label} className="flex items-center gap-1">
                <div
                  className="w-4 h-3 rounded-sm flex items-center justify-center"
                  style={{ backgroundColor: bg, border: `1px solid ${border}` }}
                >
                  <span className="text-[6px] font-bold" style={{ fontFamily: "var(--font-jetbrains)", color: text }}>
                    {effToLabel(eff)}
                  </span>
                </div>
                <span className="text-[8px] text-text-muted" style={{ fontFamily: "var(--font-dm-sans)" }}>
                  {label}
                </span>
              </div>
            );
          })}
        </div>

        <div className="p-4 space-y-5">
          {/* Weaknesses */}
          {weaknesses.length > 0 && (
            <section>
              <SectionHeader label="VULNERABLE" color="#f87171" count={weaknesses.length} />
              <div className="space-y-1">
                {weaknesses.map(({ type, effSlots }) => (
                  <WeaknessRow key={type} type={type} slots={effSlots} />
                ))}
              </div>
            </section>
          )}

          {/* Immunities */}
          {immunities.length > 0 && (
            <section>
              <SectionHeader label="IMMUNE" color="#60a5fa" count={immunities.length} />
              <div className="flex flex-wrap gap-1.5">
                {immunities.map(({ type }) => (
                  <TypeBadge key={type} type={type} size="sm" />
                ))}
              </div>
            </section>
          )}

          {/* Resistances */}
          {resistOnly.length > 0 && (
            <section>
              <SectionHeader label="RESISTS" color="#4ade80" count={resistOnly.length} />
              <div className="flex flex-wrap gap-1.5">
                {resistOnly.map(({ type }) => (
                  <TypeBadge key={type} type={type} size="sm" />
                ))}
              </div>
            </section>
          )}

          {weaknesses.length === 0 && resisted.length === 0 && (
            <p className="text-xs text-text-muted text-center py-4" style={{ fontFamily: "var(--font-dm-sans)" }}>
              Add more Pokémon to see coverage patterns.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
