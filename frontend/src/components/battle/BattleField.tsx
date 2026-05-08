"use client";
import type {
  BattlePlayerState,
  FieldState,
  SideState,
  StatStages,
} from "@/src/hooks/useBattleWS";
import { HPBar } from "./HPBar";
import { PokemonSprite } from "./PokemonSprite";
import { TeamDots } from "./TeamDots";

// ─── Constants ───────────────────────────────────────────────────────────────

const STATUS_BADGE: Record<string, { text: string; color: string }> = {
  burn: { text: "BRN", color: "#f97316" },
  paralysis: { text: "PAR", color: "#eab308" },
  poison: { text: "PSN", color: "#a855f7" },
  toxic: { text: "TOX", color: "#7c3aed" },
  sleep: { text: "SLP", color: "#94a3b8" },
  freeze: { text: "FRZ", color: "#06b6d4" },
};

const WEATHER_INFO: Record<
  string,
  { label: string; icon: string; color: string }
> = {
  sun: { label: "SUN", icon: "\u2600", color: "#f59e0b" },
  rain: { label: "RAIN", icon: "\u{1F327}", color: "#3b82f6" },
  sandstorm: { label: "SAND", icon: "\u{1F32A}", color: "#d97706" },
  hail: { label: "HAIL", icon: "\u2744", color: "#06b6d4" },
};

const TERRAIN_INFO: Record<string, { label: string; color: string }> = {
  electric: { label: "ELECTRIC TERRAIN", color: "#eab308" },
  grassy: { label: "GRASSY TERRAIN", color: "#22c55e" },
  psychic: { label: "PSYCHIC TERRAIN", color: "#ec4899" },
  misty: { label: "MISTY TERRAIN", color: "#c084fc" },
};

const STAT_SHORT: { key: keyof StatStages; label: string }[] = [
  { key: "attack", label: "ATK" },
  { key: "defense", label: "DEF" },
  { key: "special_attack", label: "SPA" },
  { key: "special_defense", label: "SPD" },
  { key: "speed", label: "SPE" },
  { key: "accuracy", label: "ACC" },
  { key: "evasion", label: "EVA" },
];

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatStageIndicator({ stages }: { stages: StatStages }) {
  const active = STAT_SHORT.filter((s) => stages[s.key] !== 0);
  if (active.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-0.5">
      {active.map(({ key, label }) => {
        const val = stages[key];
        const up = val > 0;
        return (
          <span
            key={key}
            className="text-[6px] font-bold px-1 py-px rounded-sm leading-none"
            style={{
              fontFamily: "var(--font-jetbrains)",
              backgroundColor: up
                ? "rgba(74,222,128,0.1)"
                : "rgba(248,113,113,0.1)",
              color: up ? "#4ade80" : "#f87171",
              border: `1px solid ${up ? "rgba(74,222,128,0.2)" : "rgba(248,113,113,0.2)"}`,
            }}
          >
            {label}
            {up ? "+" : ""}
            {val}
          </span>
        );
      })}
    </div>
  );
}

function HazardIndicators({ side }: { side: SideState }) {
  const hazards: { label: string; color: string }[] = [];

  if (side.stealth_rock) hazards.push({ label: "SR", color: "#a8a29e" });
  if (side.spikes > 0)
    hazards.push({ label: `Spikes \u00d7${side.spikes}`, color: "#78716c" });
  if (side.toxic_spikes > 0)
    hazards.push({
      label: `T.Spikes \u00d7${side.toxic_spikes}`,
      color: "#a855f7",
    });
  if (side.sticky_web) hazards.push({ label: "Web", color: "#eab308" });
  if (side.reflect > 0)
    hazards.push({ label: `Reflect ${side.reflect}`, color: "#f87171" });
  if (side.light_screen > 0)
    hazards.push({
      label: `L.Screen ${side.light_screen}`,
      color: "#60a5fa",
    });
  if (side.tailwind > 0)
    hazards.push({ label: `Tailwind ${side.tailwind}`, color: "#38bdf8" });

  if (hazards.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-0.5">
      {hazards.map((h) => (
        <span
          key={h.label}
          className="text-[6.5px] font-bold px-1.5 py-0.5 rounded"
          style={{
            fontFamily: "var(--font-jetbrains)",
            backgroundColor: `${h.color}12`,
            color: h.color,
            border: `1px solid ${h.color}25`,
          }}
        >
          {h.label}
        </span>
      ))}
    </div>
  );
}

function PlayerSide({
  player,
  isMe,
  side,
}: {
  player: BattlePlayerState;
  isMe: boolean;
  side?: SideState;
}) {
  const mon = player.team[player.active_index];
  const accentColor = isMe ? "#f87171" : "#60a5fa";

  if (!mon) return null;

  const statusInfo =
    mon.status && mon.status !== "none" ? STATUS_BADGE[mon.status] : null;

  return (
    <div
      className={`flex-1 flex flex-col ${isMe ? "items-end" : "items-start"} gap-2`}
    >
      {/* Info panel */}
      <div
        className={`w-full max-w-[240px] ${isMe ? "text-right" : "text-left"}`}
      >
        {/* Label + dex number */}
        <div
          className={`flex items-center gap-2 mb-1 ${isMe ? "justify-end" : "justify-start"}`}
        >
          <span
            className="text-[7px] font-bold tracking-[0.25em] uppercase"
            style={{
              fontFamily: "var(--font-unbounded)",
              color: `${accentColor}90`,
            }}
          >
            {isMe ? "YOU" : "OPPONENT"}
          </span>
          <span
            className="text-[7px] text-text-muted tabular-nums"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            #{String(mon.species_id).padStart(3, "0")}
          </span>
        </div>

        {/* Name + Status */}
        <div
          className={`flex items-center gap-1.5 mb-0.5 flex-wrap ${isMe ? "justify-end" : ""}`}
        >
          <p
            className="text-sm font-bold text-text-primary capitalize"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            {mon.name.replace(/-/g, " ")}
          </p>
          {statusInfo && (
            <span
              className="text-[6.5px] font-bold px-1.5 py-0.5 rounded"
              style={{
                backgroundColor: `${statusInfo.color}20`,
                color: statusInfo.color,
                fontFamily: "var(--font-jetbrains)",
              }}
            >
              {statusInfo.text}
            </span>
          )}
        </div>

        {/* Ability + Item */}
        {(mon.ability || mon.item) && (
          <p
            className="text-[7.5px] text-text-muted capitalize mb-1.5"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {mon.ability ? mon.ability.replace(/-/g, " ") : ""}
            {mon.ability && mon.item ? " \u00b7 " : ""}
            {mon.item ? mon.item.replace(/-/g, " ") : ""}
          </p>
        )}

        {/* HP */}
        <HPBar current={mon.current_hp} max={mon.max_hp} size="md" />

        {/* Stat stages */}
        {mon.stat_stages && (
          <div className={`mt-1.5 ${isMe ? "flex justify-end" : ""}`}>
            <StatStageIndicator stages={mon.stat_stages} />
          </div>
        )}

        {/* Team dots */}
        <div className={`mt-2 ${isMe ? "flex justify-end" : ""}`}>
          <TeamDots
            team={player.team}
            activeIndex={player.active_index}
            color={accentColor}
          />
        </div>

        {/* Hazards */}
        {side && (
          <div className={`mt-1.5 ${isMe ? "flex justify-end" : ""}`}>
            <HazardIndicators side={side} />
          </div>
        )}
      </div>

      {/* Sprite */}
      <div className="flex justify-center w-full">
        <PokemonSprite
          speciesId={mon.species_id}
          name={mon.name}
          fainted={mon.fainted}
          size={isMe ? 160 : 136}
          flip={isMe}
        />
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

interface BattleFieldProps {
  myPlayer: BattlePlayerState;
  opponentPlayer: BattlePlayerState;
  mySide?: SideState;
  opponentSide?: SideState;
  turn: number;
  field?: FieldState;
}

export function BattleField({
  myPlayer,
  opponentPlayer,
  mySide,
  opponentSide,
  turn,
  field,
}: BattleFieldProps) {
  const weatherKey =
    field?.weather && field.weather !== "none" ? field.weather : null;
  const terrainKey =
    field?.terrain && field.terrain !== "none" ? field.terrain : null;
  const weatherInfo = weatherKey ? WEATHER_INFO[weatherKey] : null;
  const terrainInfo = terrainKey ? TERRAIN_INFO[terrainKey] : null;

  return (
    <div className="relative rounded-2xl border border-bg-border bg-bg-surface overflow-hidden">
      {/* ── Background layers ── */}

      {/* Grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(108,99,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(108,99,255,1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Arena radial gradient — depth */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 90%, rgba(108,99,255,0.05) 0%, transparent 55%)",
        }}
      />

      {/* Weather tint overlay */}
      {weatherInfo && (
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-700"
          style={{ backgroundColor: weatherInfo.color, opacity: 0.04 }}
        />
      )}

      {/* Center line */}
      <div
        className="absolute left-1/2 top-10 bottom-4 w-px -translate-x-1/2 pointer-events-none"
        style={{
          background:
            "linear-gradient(to bottom, transparent, rgba(255,255,255,0.04), transparent)",
        }}
      />

      {/* ── Top badges ── */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2">
        <div
          className="px-3 py-1 rounded-full border text-[7.5px] font-bold tracking-widest tabular-nums"
          style={{
            fontFamily: "var(--font-jetbrains)",
            backgroundColor: "rgba(108,99,255,0.1)",
            borderColor: "rgba(108,99,255,0.25)",
            color: "#6c63ff",
          }}
        >
          TURN {turn}
        </div>
        {weatherInfo && field && (
          <div
            className="px-2.5 py-1 rounded-full border text-[7.5px] font-bold tracking-wider tabular-nums"
            style={{
              fontFamily: "var(--font-jetbrains)",
              backgroundColor: `${weatherInfo.color}15`,
              borderColor: `${weatherInfo.color}35`,
              color: weatherInfo.color,
            }}
          >
            {weatherInfo.icon} {weatherInfo.label} ({field.weather_turns})
          </div>
        )}
        {terrainInfo && field && (
          <div
            className="px-2.5 py-1 rounded-full border text-[7.5px] font-bold tracking-wider tabular-nums"
            style={{
              fontFamily: "var(--font-jetbrains)",
              backgroundColor: `${terrainInfo.color}15`,
              borderColor: `${terrainInfo.color}35`,
              color: terrainInfo.color,
            }}
          >
            {terrainInfo.label} ({field.terrain_turns})
          </div>
        )}
      </div>

      {/* ── Arena ── */}
      <div className="relative flex items-end justify-between px-6 sm:px-10 pt-12 pb-6 gap-6">
        <PlayerSide
          player={opponentPlayer}
          isMe={false}
          side={opponentSide}
        />
        <PlayerSide player={myPlayer} isMe={true} side={mySide} />
      </div>
    </div>
  );
}
