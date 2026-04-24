"use client";

import Link from "next/link";
import { ArrowLeft, Swords } from "lucide-react";
import { useAuth } from "@/src/contexts/AuthContext";
import { useBattleHistory } from "@/src/hooks/useProfile";
import type { BattleHistoryItem } from "@/src/lib/api";

type Result = "win" | "loss" | "draw";

function getResult(item: BattleHistoryItem, userId: string): Result {
  if (item.winner_id === null) return "draw";
  if (item.winner_id === userId) return "win";
  return "loss";
}

function getOpponent(item: BattleHistoryItem, userId: string): string {
  const opponentId = item.player1_id === userId ? item.player2_id : item.player1_id;
  const opponentUsername = item.player1_id === userId ? item.player2_username : item.player1_username;
  void opponentId;
  return opponentUsername ?? "Unknown Trainer";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const RESULT_STYLES: Record<Result, { label: string; badge: string; border: string; glow: string }> = {
  win: {
    label: "WIN",
    badge: "bg-green-400/10 text-green-400 border border-green-400/25",
    border: "border-green-400/15",
    glow: "shadow-[0_0_0_1px_rgba(74,222,128,0.08)]",
  },
  loss: {
    label: "LOSS",
    badge: "bg-red-400/10 text-red-400 border border-red-400/25",
    border: "border-red-400/15",
    glow: "shadow-[0_0_0_1px_rgba(248,113,113,0.08)]",
  },
  draw: {
    label: "DRAW",
    badge: "bg-slate-400/10 text-slate-400 border border-slate-400/20",
    border: "border-bg-border",
    glow: "",
  },
};

function ResultBadge({ result }: { result: Result }) {
  const s = RESULT_STYLES[result];
  return (
    <span
      className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-md text-[9px] font-black tracking-[0.2em] tabular-nums ${s.badge}`}
      style={{ fontFamily: "var(--font-unbounded)" }}
    >
      {s.label}
    </span>
  );
}

function StatCard({ label, value, valueClass }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex-1 min-w-0 bg-bg-elevated border border-bg-border rounded-xl px-3 py-3 flex flex-col gap-1">
      <p
        className="text-[8px] text-text-muted tracking-[0.22em] uppercase truncate"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {label}
      </p>
      <p
        className={`text-xl font-black tabular-nums leading-none ${valueClass ?? "text-text-primary"}`}
        style={{ fontFamily: "var(--font-jetbrains)" }}
      >
        {value}
      </p>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-bg-surface border border-bg-border rounded-xl px-5 py-4 flex items-center gap-4">
      <div className="shimmer w-14 h-6 rounded-md" />
      <div className="flex-1 space-y-2">
        <div className="shimmer w-40 h-4 rounded" />
        <div className="shimmer w-24 h-3 rounded" />
      </div>
      <div className="shimmer w-16 h-4 rounded" />
    </div>
  );
}

export default function BattleHistoryPage() {
  const { user, loading: authLoading } = useAuth();
  const { data: history, isLoading } = useBattleHistory();

  if (authLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-text-muted text-sm" style={{ fontFamily: "var(--font-dm-sans)" }}>
          Sign in to view your battle history.
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

  const battles = history ?? [];
  const wins = battles.filter((b) => getResult(b, user.id) === "win").length;
  const losses = battles.filter((b) => getResult(b, user.id) === "loss").length;
  const winRate = battles.length > 0 ? Math.round((wins / battles.length) * 100) : null;
  const winRateDisplay = winRate !== null ? `${winRate}%` : "—";
  const winRateClass =
    winRate === null
      ? "text-text-muted"
      : winRate >= 50
      ? "text-green-400"
      : "text-red-400";

  return (
    <div className="min-h-[calc(100vh-4rem)] pt-20 pb-16 px-4">
      <div className="mx-auto max-w-2xl">

        {/* Back link */}
        <Link
          href="/battle"
          className="inline-flex items-center gap-1.5 text-[10px] text-text-muted hover:text-text-secondary transition-colors mb-8 group"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          <ArrowLeft size={11} className="group-hover:-translate-x-0.5 transition-transform" />
          BACK TO BATTLE
        </Link>

        {/* Header */}
        <div className="mb-8">
          <p
            className="text-[9px] text-text-muted tracking-[0.3em] mb-1.5 uppercase"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            Battle History
          </p>
          <h1
            className="text-3xl font-black text-text-primary leading-none"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            YOUR BATTLES
          </h1>
        </div>

        {/* Stats row */}
        <div className="flex gap-3 mb-8">
          <StatCard label="Total" value={String(battles.length)} />
          <StatCard label="Wins" value={String(wins)} valueClass="text-green-400" />
          <StatCard label="Losses" value={String(losses)} valueClass="text-red-400" />
          <StatCard label="Win Rate" value={winRateDisplay} valueClass={winRateClass} />
        </div>

        {/* Battle list */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : battles.length === 0 ? (
          <div className="bg-bg-surface border border-bg-border rounded-2xl px-6 py-12 flex flex-col items-center gap-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-bg-elevated border border-bg-border flex items-center justify-center">
              <Swords size={24} className="text-text-muted" strokeWidth={1.5} />
            </div>
            <div>
              <p
                className="text-sm font-bold text-text-secondary mb-1"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                NO BATTLES YET
              </p>
              <p
                className="text-xs text-text-muted"
                style={{ fontFamily: "var(--font-dm-sans)" }}
              >
                Your battle record will appear here after your first match.
              </p>
            </div>
            <Link
              href="/battle"
              className="mt-2 px-5 py-2.5 rounded-xl bg-accent hover:bg-accent/90 text-white text-xs font-bold transition-all"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              FIND A BATTLE
            </Link>
          </div>
        ) : (
          <div className="space-y-2.5">
            {battles.map((item) => {
              const result = getResult(item, user.id);
              const opponent = getOpponent(item, user.id);
              const s = RESULT_STYLES[result];

              return (
                <div
                  key={item.id}
                  className={`bg-bg-surface border rounded-xl px-5 py-4 flex items-center gap-4 transition-all hover:bg-bg-elevated ${s.border} ${s.glow}`}
                >
                  <ResultBadge result={result} />

                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm text-text-primary truncate"
                      style={{ fontFamily: "var(--font-dm-sans)" }}
                    >
                      vs{" "}
                      <span className="font-semibold">
                        @{opponent}
                      </span>
                    </p>
                    <p
                      className="text-[10px] text-text-muted mt-0.5"
                      style={{ fontFamily: "var(--font-jetbrains)" }}
                    >
                      {item.turns} {item.turns === 1 ? "turn" : "turns"}
                    </p>
                  </div>

                  <p
                    className="text-[10px] text-text-muted shrink-0"
                    style={{ fontFamily: "var(--font-jetbrains)" }}
                  >
                    {formatDate(item.created_at)}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
