"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Pencil, Check, X, ArrowRight } from "lucide-react";
import { useAuth } from "@/src/contexts/AuthContext";
import { useMyProfile, useCreateProfile, useUpdateProfile, useBattleHistory } from "@/src/hooks/useProfile";

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <h3
        className="text-[9px] font-bold text-text-muted tracking-[0.25em] uppercase"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {children}
      </h3>
      <div className="flex-1 h-px bg-bg-border" />
    </div>
  );
}

function SetupForm() {
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const createProfile = useCreateProfile();
  const router = useRouter();

  const usernameValid = /^[a-zA-Z0-9_]{3,20}$/.test(username);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!usernameValid) {
      setError("Username must be 3–20 characters: letters, numbers, underscores only.");
      return;
    }
    try {
      await createProfile.mutateAsync({ username });
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create profile");
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-8">
          <div className="relative">
            <div className="w-16 h-16 rounded-full border-4 border-accent flex items-center justify-center">
              <div className="w-7 h-7 rounded-full bg-accent" />
            </div>
            <div className="absolute top-1/2 left-0 right-0 h-px bg-accent/60 -translate-y-px" />
          </div>
        </div>

        <div className="bg-bg-surface border border-bg-border rounded-2xl p-8">
          <p
            className="text-[10px] text-accent tracking-[0.3em] mb-2 text-center"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            KANTOVISION
          </p>
          <h1 className="text-2xl font-black text-text-primary text-center mb-1" style={{ fontFamily: "var(--font-unbounded)" }}>
            CHOOSE YOUR
          </h1>
          <h1 className="text-2xl font-black text-accent text-center mb-6" style={{ fontFamily: "var(--font-unbounded)" }}>
            TRAINER NAME
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted text-sm" style={{ fontFamily: "var(--font-jetbrains)" }}>
                @
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setError(""); }}
                placeholder="trainer_name"
                maxLength={20}
                className="w-full bg-bg-elevated border border-bg-border rounded-xl pl-8 pr-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/50 transition-colors"
                style={{ fontFamily: "var(--font-jetbrains)" }}
                autoFocus
              />
              {username && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {usernameValid ? <Check size={14} className="text-green-400" /> : <X size={14} className="text-red-400" />}
                </div>
              )}
            </div>

            <p className="text-[10px] text-text-muted" style={{ fontFamily: "var(--font-dm-sans)" }}>
              3–20 characters. Letters, numbers, and underscores only.
            </p>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                <p className="text-xs text-red-400" style={{ fontFamily: "var(--font-dm-sans)" }}>{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={!usernameValid || createProfile.isPending}
              className="w-full py-3 rounded-xl bg-accent hover:bg-accent/90 disabled:bg-accent/30 disabled:cursor-not-allowed text-white text-sm font-bold transition-all"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {createProfile.isPending ? "CREATING..." : "CREATE PROFILE"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const { data: profile, isLoading } = useMyProfile();
  const updateProfile = useUpdateProfile();
  const { data: battleHistory } = useBattleHistory();

  const [editingDisplayName, setEditingDisplayName] = useState(false);
  const [displayNameInput, setDisplayNameInput] = useState("");

  if (authLoading || isLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!user) { router.push("/auth"); return null; }
  if (!profile) return <SetupForm />;

  const initials = profile.username.slice(0, 2).toUpperCase();
  const emailPrefix = user.email?.split("@")[0] ?? "";

  const battles = battleHistory ?? [];
  const wins = battles.filter((b) => b.winner_id === user.id).length;
  const losses = battles.filter((b) => b.winner_id !== null && b.winner_id !== user.id).length;
  const winRate = battles.length > 0 ? Math.round((wins / battles.length) * 100) : null;

  async function handleSaveDisplayName() {
    const val = displayNameInput.trim() || null;
    try {
      await updateProfile.mutateAsync(val);
      setEditingDisplayName(false);
    } catch { /* keep editing open */ }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] pt-20 pb-12 px-4">
      <div className="mx-auto max-w-lg">
        <div className="mb-8">
          <p className="text-[10px] text-text-muted tracking-[0.3em] mb-1" style={{ fontFamily: "var(--font-unbounded)" }}>
            TRAINER PROFILE
          </p>
        </div>

        <div className="bg-bg-surface border border-bg-border rounded-2xl p-6">
          <div className="flex flex-col items-center text-center">
            <div className="w-20 h-20 rounded-full bg-accent/20 border-2 border-accent/50 flex items-center justify-center mb-4">
              <span className="text-2xl font-black text-accent" style={{ fontFamily: "var(--font-unbounded)" }}>
                {initials}
              </span>
            </div>
            <p className="text-lg font-black text-text-primary leading-tight" style={{ fontFamily: "var(--font-unbounded)" }}>
              @{profile.username}
            </p>
            <p className="text-xs text-text-muted mt-0.5" style={{ fontFamily: "var(--font-dm-sans)" }}>
              {emailPrefix}
            </p>
          </div>

          <div className="mt-5 pt-5 border-t border-bg-border">
            <SectionTitle>Display Name</SectionTitle>
            {editingDisplayName ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={displayNameInput}
                  onChange={(e) => setDisplayNameInput(e.target.value)}
                  placeholder="Optional display name"
                  maxLength={40}
                  className="flex-1 bg-bg-elevated border border-bg-border rounded-lg px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/50 transition-colors"
                  style={{ fontFamily: "var(--font-dm-sans)" }}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSaveDisplayName();
                    if (e.key === "Escape") setEditingDisplayName(false);
                  }}
                />
                <button onClick={handleSaveDisplayName} disabled={updateProfile.isPending} className="p-1.5 rounded-lg bg-accent/20 hover:bg-accent/30 text-accent transition-colors">
                  <Check size={13} />
                </button>
                <button onClick={() => setEditingDisplayName(false)} className="p-1.5 rounded-lg hover:bg-bg-elevated text-text-muted transition-colors">
                  <X size={13} />
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <p className="text-sm text-text-secondary" style={{ fontFamily: "var(--font-dm-sans)" }}>
                  {profile.display_name ?? <span className="text-text-muted italic">Not set</span>}
                </p>
                <button
                  onClick={() => { setDisplayNameInput(profile.display_name ?? ""); setEditingDisplayName(true); }}
                  className="p-1 rounded hover:bg-bg-elevated text-text-muted hover:text-text-primary transition-colors"
                >
                  <Pencil size={12} />
                </button>
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-bg-border">
            <SectionTitle>Battle Record</SectionTitle>
            <div className="grid grid-cols-4 gap-2 mb-3">
              {[
                { label: "Battles", value: String(battles.length), cls: "text-text-primary" },
                { label: "Wins", value: String(wins), cls: "text-green-400" },
                { label: "Losses", value: String(losses), cls: "text-red-400" },
                {
                  label: "Win Rate",
                  value: winRate !== null ? `${winRate}%` : "—",
                  cls: winRate === null ? "text-text-muted" : winRate >= 50 ? "text-green-400" : "text-red-400",
                },
              ].map(({ label, value, cls }) => (
                <div key={label} className="bg-bg-elevated border border-bg-border rounded-lg px-2 py-2.5 flex flex-col gap-1">
                  <p className="text-[7px] text-text-muted tracking-[0.2em] uppercase" style={{ fontFamily: "var(--font-unbounded)" }}>
                    {label}
                  </p>
                  <p className={`text-base font-black tabular-nums leading-none ${cls}`} style={{ fontFamily: "var(--font-jetbrains)" }}>
                    {value}
                  </p>
                </div>
              ))}
            </div>
            <Link
              href="/battle/history"
              className="inline-flex items-center gap-1 text-[10px] text-text-muted hover:text-accent transition-colors group"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              BATTLE HISTORY
              <ArrowRight size={10} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          <div className="mt-4 pt-4 border-t border-bg-border">
            <p className="text-[9px] text-text-muted" style={{ fontFamily: "var(--font-jetbrains)" }}>
              JOINED {new Date(profile.created_at).toLocaleDateString("en-US", {
                month: "short", year: "numeric",
              }).toUpperCase()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
