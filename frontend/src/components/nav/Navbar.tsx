"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/src/lib/utils";
import { BookOpen, Users, Scan, Swords, LogIn, LogOut, ChevronDown, User } from "lucide-react";
import { useAuth } from "@/src/contexts/AuthContext";

const TABS = [
  { href: "/pokedex", label: "Pokédex", icon: BookOpen },
  { href: "/team", label: "Team Builder", icon: Users },
  { href: "/battle", label: "Battle", icon: Swords },
  { href: "/scan", label: "AI Scanner", icon: Scan },
];

const AUTH_TABS = [
  { href: "/profile", label: "Profile", icon: User },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut, loading } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleSignOut() {
    setDropdownOpen(false);
    await signOut();
    router.push("/pokedex");
  }

  const emailPrefix = user?.email?.split("@")[0] ?? "";

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-bg-border bg-bg-base/80 backdrop-blur-md">
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
        {/* Logo */}
        <Link href="/pokedex" className="flex items-center gap-2 group">
          <div className="relative">
            <div className="w-7 h-7 rounded-full border-2 border-accent flex items-center justify-center group-hover:border-accent/80 transition-colors">
              <div className="w-3 h-3 rounded-full bg-accent group-hover:bg-accent/80 transition-colors" />
            </div>
            <div className="absolute -top-0.5 left-3 right-0 h-px bg-accent/40" />
          </div>
          <span
            className="text-sm font-display font-bold tracking-widest text-text-primary"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            KANTOVISION
          </span>
        </Link>

        {/* Tabs */}
        <div className="flex items-center gap-1">
          {[...TABS, ...(user ? AUTH_TABS : [])].map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "relative flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200",
                  active
                    ? "text-text-primary"
                    : "text-text-secondary hover:text-text-primary"
                )}
              >
                {active && (
                  <span className="absolute inset-0 rounded-md bg-accent/10 border border-accent/20" />
                )}
                <Icon size={15} strokeWidth={1.5} />
                <span style={{ fontFamily: "var(--font-dm-sans)" }}>{label}</span>
              </Link>
            );
          })}
        </div>

        {/* Right side: Gen badge + auth */}
        <div className="flex items-center gap-3">
          <span
            className="text-xs text-text-muted border border-bg-border px-3 py-1 rounded-full"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            GEN I–IX
          </span>

          {!loading && (
            user ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen((v) => !v)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-bg-border bg-bg-elevated hover:border-accent/30 transition-all group"
                >
                  {/* Avatar initials */}
                  <div className="w-6 h-6 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center">
                    <span
                      className="text-[9px] font-bold text-accent"
                      style={{ fontFamily: "var(--font-unbounded)" }}
                    >
                      {emailPrefix.slice(0, 2).toUpperCase()}
                    </span>
                  </div>
                  <span
                    className="text-xs text-text-secondary group-hover:text-text-primary transition-colors max-w-[100px] truncate"
                    style={{ fontFamily: "var(--font-dm-sans)" }}
                  >
                    {emailPrefix}
                  </span>
                  <ChevronDown size={12} className={cn("text-text-muted transition-transform", dropdownOpen && "rotate-180")} />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 top-full mt-2 w-44 bg-bg-elevated border border-bg-border rounded-xl shadow-2xl overflow-hidden z-50">
                    <div className="px-3 py-2.5 border-b border-bg-border">
                      <p
                        className="text-[9px] text-text-muted tracking-widest"
                        style={{ fontFamily: "var(--font-unbounded)" }}
                      >
                        SIGNED IN AS
                      </p>
                      <p className="text-xs text-text-primary mt-0.5 truncate" style={{ fontFamily: "var(--font-dm-sans)" }}>
                        {user.email}
                      </p>
                    </div>
                    <button
                      onClick={handleSignOut}
                      className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-xs text-text-secondary hover:text-red-400 hover:bg-red-500/5 transition-colors"
                      style={{ fontFamily: "var(--font-dm-sans)" }}
                    >
                      <LogOut size={13} />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                href="/auth"
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-accent/30 bg-accent/5 hover:bg-accent/10 text-accent text-xs font-medium transition-all"
                style={{ fontFamily: "var(--font-dm-sans)" }}
              >
                <LogIn size={13} />
                Sign in
              </Link>
            )
          )}
        </div>
      </div>
    </nav>
  );
}
