"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/src/lib/supabase";
import { useAuth } from "@/src/contexts/AuthContext";
import { Eye, EyeOff, LogIn, UserPlus, AlertCircle } from "lucide-react";

export default function AuthPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && user) router.replace("/team");
  }, [user, loading, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);

    try {
      if (mode === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.replace("/team");
      } else {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setSuccess("Check your email to confirm your account, then sign in.");
        setMode("login");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4">
      {/* Background grid */}
      <div className="pointer-events-none fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage: "linear-gradient(var(--color-bg-border) 1px, transparent 1px), linear-gradient(90deg, var(--color-bg-border) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Glow */}
        <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-accent/20 via-transparent to-transparent pointer-events-none" />

        <div className="relative bg-bg-surface border border-bg-border rounded-2xl overflow-hidden shadow-2xl">
          {/* Header strip */}
          <div className="relative overflow-hidden px-8 pt-8 pb-6 border-b border-bg-border">
            <div className="absolute inset-0 opacity-10" style={{ background: "radial-gradient(ellipse at 50% 0%, #6c63ff 0%, transparent 70%)" }} />
            <div className="relative">
              {/* Logo mark */}
              <div className="flex items-center gap-2 mb-5">
                <div className="relative">
                  <div className="w-6 h-6 rounded-full border-2 border-accent flex items-center justify-center">
                    <div className="w-2.5 h-2.5 rounded-full bg-accent" />
                  </div>
                  <div className="absolute -top-0.5 left-2.5 right-0 h-px bg-accent/40" />
                </div>
                <span
                  className="text-xs font-bold tracking-widest text-text-primary"
                  style={{ fontFamily: "var(--font-unbounded)" }}
                >
                  KANTOVISION
                </span>
              </div>
              <h1
                className="text-2xl font-black text-text-primary tracking-tight"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                {mode === "login" ? "WELCOME\nBACK" : "CREATE\nACCOUNT"}
              </h1>
              <p className="text-[11px] text-text-muted mt-2" style={{ fontFamily: "var(--font-jetbrains)" }}>
                {mode === "login"
                  ? "Sign in to access your saved teams"
                  : "Start building your competitive roster"}
              </p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-8 py-6 space-y-4">
            {error && (
              <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                <AlertCircle size={13} className="shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {error}
                </p>
              </div>
            )}
            {success && (
              <div className="flex items-start gap-2.5 p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400">
                <p className="text-[11px] leading-relaxed" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {success}
                </p>
              </div>
            )}

            <div className="space-y-1.5">
              <label
                className="block text-[9px] tracking-widest text-text-muted"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                EMAIL
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="trainer@pokecenter.com"
                className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
              />
            </div>

            <div className="space-y-1.5">
              <label
                className="block text-[9px] tracking-widest text-text-muted"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                PASSWORD
              </label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  placeholder="••••••••"
                  className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-3.5 pr-10 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
                >
                  {showPass ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs tracking-widest py-3 rounded-lg transition-all mt-2"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {submitting ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : mode === "login" ? (
                <>
                  <LogIn size={13} />
                  SIGN IN
                </>
              ) : (
                <>
                  <UserPlus size={13} />
                  CREATE ACCOUNT
                </>
              )}
            </button>
          </form>

          {/* Mode toggle */}
          <div className="px-8 pb-7 flex items-center justify-center gap-1.5">
            <span className="text-[11px] text-text-muted" style={{ fontFamily: "var(--font-dm-sans)" }}>
              {mode === "login" ? "Don't have an account?" : "Already have an account?"}
            </span>
            <button
              onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(null); setSuccess(null); }}
              className="text-[11px] text-accent hover:text-accent/80 font-semibold transition-colors"
              style={{ fontFamily: "var(--font-dm-sans)" }}
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
