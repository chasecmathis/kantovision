"use client";
import { useEffect } from "react";
import { Trophy, Frown, Flag, AlertTriangle } from "lucide-react";
import { useBattleWS } from "@/src/hooks/useBattleWS";
import { useAuth } from "@/src/contexts/AuthContext";
import { MatchmakingLobby } from "@/src/components/battle/MatchmakingLobby";
import { BattleField } from "@/src/components/battle/BattleField";
import { BattleLog } from "@/src/components/battle/BattleLog";
import { ActionPanel } from "@/src/components/battle/ActionPanel";
import Link from "next/link";

export default function BattlePage() {
  const { user } = useAuth();
  const {
    phase,
    battleState,
    log,
    myUserId,
    endInfo,
    waitingForOpponent,
    opponentDisconnected,
    opponentDisconnectMessage,
    serverShuttingDown,
    turnStartedAt,
    connect,
    joinQueue,
    leaveQueue,
    makeMove,
    forfeit,
    disconnect,
  } = useBattleWS();

  // Connect to WS on mount if user is logged in
  useEffect(() => {
    if (user) connect();
    return () => disconnect();
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  // Redirect to auth if not logged in
  if (!user) {
    return (
      <div className="max-w-[1400px] mx-auto px-6 py-16 flex flex-col items-center gap-4">
        <p className="text-text-muted text-sm" style={{ fontFamily: "var(--font-dm-sans)" }}>
          You need to be signed in to battle.
        </p>
        <Link
          href="/auth"
          className="px-4 py-2 rounded-lg border border-accent/30 text-accent text-xs transition-all hover:bg-accent/10"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          SIGN IN
        </Link>
      </div>
    );
  }

  // ── Battle ended view ──────────────────────────────────────────────────────
  if (phase === "ended" && endInfo) {
    const iWon = endInfo.winner_id === myUserId;
    const isDraw = endInfo.winner_id === null;

    return (
      <div className="max-w-[1400px] mx-auto px-6 py-16 flex flex-col items-center gap-6">
        <div
          className="w-24 h-24 rounded-3xl flex items-center justify-center"
          style={{
            backgroundColor: isDraw
              ? "rgba(148,163,184,0.1)"
              : iWon
              ? "rgba(74,222,128,0.1)"
              : "rgba(248,113,113,0.1)",
            border: `1px solid ${isDraw ? "rgba(148,163,184,0.25)" : iWon ? "rgba(74,222,128,0.3)" : "rgba(248,113,113,0.3)"}`,
          }}
        >
          {isDraw ? (
            <Flag size={40} className="text-slate-400" strokeWidth={1.5} />
          ) : iWon ? (
            <Trophy size={40} className="text-green-400" strokeWidth={1.5} />
          ) : (
            <Frown size={40} className="text-red-400" strokeWidth={1.5} />
          )}
        </div>

        <div className="text-center">
          <h1
            className="text-4xl font-black tracking-tight mb-2"
            style={{
              fontFamily: "var(--font-unbounded)",
              color: isDraw ? "#94a3b8" : iWon ? "#4ade80" : "#f87171",
            }}
          >
            {isDraw ? "DRAW" : iWon ? "VICTORY!" : "DEFEATED"}
          </h1>
          <p className="text-sm text-text-secondary" style={{ fontFamily: "var(--font-dm-sans)" }}>
            {endInfo.reason === "forfeit" ? (iWon ? "Your opponent forfeited." : "You forfeited.") : "All Pokémon have fainted."}
          </p>
        </div>

        {/* Battle log replay */}
        {log.length > 0 && (
          <div className="w-full max-w-lg">
            <BattleLog entries={log} />
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => {
              disconnect();
              connect();
            }}
            className="px-5 py-2.5 rounded-xl border border-accent/30 bg-accent/10 text-accent text-xs font-bold transition-all hover:bg-accent/20"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            PLAY AGAIN
          </button>
          <Link
            href="/team"
            className="px-5 py-2.5 rounded-xl border border-bg-border bg-bg-elevated text-text-secondary text-xs hover:text-text-primary hover:border-accent/30 transition-all"
            style={{ fontFamily: "var(--font-dm-sans)" }}
          >
            Edit Team
          </Link>
        </div>
      </div>
    );
  }

  // ── Active battle view ─────────────────────────────────────────────────────
  if ((phase === "active" || phase === "matched") && battleState && myUserId) {
    const myPlayer =
      battleState.player1.user_id === myUserId ? battleState.player1 : battleState.player2;
    const opponentPlayer =
      battleState.player1.user_id === myUserId ? battleState.player2 : battleState.player1;
    const myActiveMon = myPlayer.team[myPlayer.active_index];

    return (
      <div className="max-w-[1400px] mx-auto px-6 py-6 flex flex-col gap-4 min-h-[calc(100vh-64px)]">
        {/* Server shutdown warning */}
        {serverShuttingDown && (
          <div
            className="w-full px-4 py-2.5 rounded-lg border flex items-center gap-2.5 text-xs animate-fade-in"
            style={{
              borderColor: "rgba(251,146,60,0.35)",
              backgroundColor: "rgba(251,146,60,0.08)",
              color: "#fb923c",
              fontFamily: "var(--font-dm-sans)",
            }}
          >
            <AlertTriangle size={13} className="shrink-0" />
            <span>Server is restarting — your current battle may be interrupted. Results are saved.</span>
          </div>
        )}

        {/* Opponent disconnect banner */}
        {opponentDisconnected && (
          <div
            className="w-full px-4 py-2 rounded-lg border text-xs text-center"
            style={{
              borderColor: "rgba(234,179,8,0.3)",
              backgroundColor: "rgba(234,179,8,0.08)",
              color: "#eab308",
              fontFamily: "var(--font-dm-sans)",
            }}
          >
            {opponentDisconnectMessage}
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p
              className="text-xs text-text-muted tracking-[0.3em] mb-1"
              style={{ fontFamily: "var(--font-jetbrains)" }}
            >
              {'// BATTLE'}
            </p>
            <h1
              className="text-2xl font-black text-text-primary tracking-tight"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              TURN {battleState.turn}
            </h1>
          </div>
          <button
            onClick={forfeit}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-bg-border bg-bg-elevated text-text-muted hover:text-red-400 hover:border-red-500/30 text-xs transition-all"
            style={{ fontFamily: "var(--font-dm-sans)" }}
          >
            <Flag size={12} />
            Forfeit
          </button>
        </div>

        {/* Field */}
        <BattleField
          myPlayer={myPlayer}
          opponentPlayer={opponentPlayer}
          turn={battleState.turn}
        />

        {/* Bottom: log + actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BattleLog entries={log} />
          <ActionPanel
            moves={myActiveMon?.moves ?? []}
            disabled={myActiveMon?.fainted}
            waitingForOpponent={waitingForOpponent}
            onSelectMove={makeMove}
            turnKey={battleState.turn}
            turnStartedAt={turnStartedAt}
          />
        </div>
      </div>
    );
  }

  // ── Lobby / matchmaking view ───────────────────────────────────────────────
  return (
    <div className="max-w-[1400px] mx-auto px-6">
      {serverShuttingDown && (
        <div
          className="mt-6 px-4 py-2.5 rounded-lg border flex items-center gap-2.5 text-xs animate-fade-in"
          style={{
            borderColor: "rgba(251,146,60,0.35)",
            backgroundColor: "rgba(251,146,60,0.08)",
            color: "#fb923c",
            fontFamily: "var(--font-dm-sans)",
          }}
        >
          <AlertTriangle size={13} className="shrink-0" />
          <span>Server is restarting — matchmaking is temporarily unavailable.</span>
        </div>
      )}
      <MatchmakingLobby
        phase={phase}
        onFindBattle={(teamId) => joinQueue(teamId)}
        onCancel={leaveQueue}
      />
    </div>
  );
}
