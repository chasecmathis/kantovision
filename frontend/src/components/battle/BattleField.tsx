"use client";
import type { BattlePlayerState } from "@/src/hooks/useBattleWS";
import { HPBar } from "./HPBar";
import { PokemonSprite } from "./PokemonSprite";
import { TeamDots } from "./TeamDots";

interface BattleFieldProps {
  myPlayer: BattlePlayerState;
  opponentPlayer: BattlePlayerState;
  turn: number;
}

function PlayerSide({
  player,
  isMe,
  label,
}: {
  player: BattlePlayerState;
  isMe: boolean;
  label: string;
}) {
  const mon = player.team[player.active_index];
  const accentColor = isMe ? "#f87171" : "#60a5fa";

  if (!mon) return null;

  console.log(mon)

  return (
    <div className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}>
      {/* Name + HP */}
      <div className={`w-full max-w-[220px] ${isMe ? "text-right" : "text-left"}`}>
        <div className="flex items-center justify-between gap-2 mb-1">
          <span
            className="text-[8px] font-bold tracking-[0.2em] uppercase"
            style={{ fontFamily: "var(--font-unbounded)", color: accentColor }}
          >
            {label}
          </span>
          <span
            className="text-[8px] text-text-muted tabular-nums"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            #{String(mon.species_id).padStart(3, "0")}
          </span>
        </div>
        <p
          className="text-sm font-bold text-text-primary capitalize mb-2"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          {mon.name.replace(/-/g, " ")}
        </p>
        <HPBar current={mon.current_hp} max={mon.max_hp} size="md" />
        <div className="mt-2">
          <TeamDots team={player.team} activeIndex={player.active_index} color={accentColor} />
        </div>
      </div>

      {/* Sprite */}
      <div className="mt-3">
        <PokemonSprite
          speciesId={mon.species_id}
          name={mon.name}
          fainted={mon.fainted}
          size={isMe ? 160 : 128}
          flip={isMe}
        />
      </div>
    </div>
  );
}

export function BattleField({ myPlayer, opponentPlayer, turn }: BattleFieldProps) {
  return (
    <div className="relative rounded-2xl border border-bg-border bg-bg-surface overflow-hidden">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(108,99,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(108,99,255,1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Turn badge */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10">
        <div
          className="px-3 py-1 rounded-full border text-[8px] font-bold tracking-widest tabular-nums"
          style={{
            fontFamily: "var(--font-jetbrains)",
            backgroundColor: "rgba(108,99,255,0.12)",
            borderColor: "rgba(108,99,255,0.3)",
            color: "#6c63ff",
          }}
        >
          TURN {turn}
        </div>
      </div>

      {/* Arena */}
      <div className="relative flex items-end justify-between px-8 pt-10 pb-6 gap-4">
        {/* Opponent — left, no flip */}
        <PlayerSide player={opponentPlayer} isMe={false} label="opponent" />

        {/* Divider */}
        <div className="flex flex-col items-center justify-center self-stretch gap-1 shrink-0">
          <div className="w-px flex-1" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
          <span
            className="text-[10px] text-text-muted font-bold"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            VS
          </span>
          <div className="w-px flex-1" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
        </div>

        {/* Me — right, flipped */}
        <PlayerSide player={myPlayer} isMe={true} label="you" />
      </div>
    </div>
  );
}
