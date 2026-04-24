"use client";
import { useState, useMemo } from "react";
import { Search, X, ChevronDown, ChevronRight } from "lucide-react";
import { useMove, usePokemon } from "@/src/hooks/usePokemon";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import {
  formatPokemonName,
  getEnglishMoveText,
  type Pokemon,
  type PokemonMove,
  type MoveDetail,
} from "@/src/lib/pokeapi";

type LearnMethod = "level-up" | "machine" | "egg" | "tutor" | "other";

const METHOD_LABELS: Record<LearnMethod, string> = {
  "level-up": "Level Up",
  machine: "TM / HM",
  egg: "Egg Move",
  tutor: "Move Tutor",
  other: "Other",
};

interface MoveEntry {
  name: string;
  method: LearnMethod;
  level: number;
}

function groupMoves(moves: PokemonMove[]): Record<LearnMethod, MoveEntry[]> {
  const groups: Record<LearnMethod, MoveEntry[]> = {
    "level-up": [], machine: [], egg: [], tutor: [], other: [],
  };
  for (const m of moves) {
    const vgd = m.version_group_details[m.version_group_details.length - 1];
    const raw = vgd?.move_learn_method?.name ?? "other";
    const known = ["level-up", "machine", "egg", "tutor"];
    const method: LearnMethod = known.includes(raw) ? (raw as LearnMethod) : "other";
    groups[method].push({ name: m.move.name, method, level: vgd?.level_learned_at ?? 0 });
  }
  groups["level-up"].sort((a, b) => a.level - b.level);
  (["machine", "egg", "tutor", "other"] as const).forEach((k) => {
    groups[k].sort((a, b) => a.name.localeCompare(b.name));
  });
  return groups;
}

function MovePreviewPanel({ name }: { name: string }) {
  const { data, isLoading } = useMove(name);

  if (isLoading) {
    return (
      <div className="space-y-1.5 p-3">
        <div className="h-3 w-24 rounded shimmer" />
        <div className="h-3 w-full rounded shimmer" />
      </div>
    );
  }
  if (!data) return null;

  const text = getEnglishMoveText(data);

  return (
    <div className="p-3 space-y-2 animate-fade-in">
      <div className="flex items-center gap-2 flex-wrap">
        <TypeBadge type={data.type.name} size="sm" />
        <span
          className="text-[9px] text-text-muted border border-bg-border px-1.5 py-0.5 rounded capitalize"
          style={{ fontFamily: "var(--font-jetbrains)" }}
        >
          {data.damage_class.name}
        </span>
        <span className="text-[10px] text-text-muted ml-auto" style={{ fontFamily: "var(--font-jetbrains)" }}>
          {data.power != null ? `PWR ${data.power}` : "—"}
          {" · "}
          {data.accuracy != null ? `ACC ${data.accuracy}` : "—"}
          {" · "}
          PP {data.pp}
        </span>
      </div>
      {text && (
        <p className="text-[10px] text-text-secondary leading-relaxed line-clamp-2">{text}</p>
      )}
    </div>
  );
}

interface MovePickerModalProps {
  pokemon: Pokemon;
  currentMoveNames: (string | null)[];
  onSelect: (moveName: string) => void;
  onClose: () => void;
}

export function MovePickerModal({ pokemon, currentMoveNames, onSelect, onClose }: MovePickerModalProps) {
  const [search, setSearch] = useState("");
  const [hovered, setHovered] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<LearnMethod>>(new Set<LearnMethod>(["level-up"]));

  // Fetch full detail to get learnable moves — the list endpoint returns moves: []
  const { data: fullPokemon, isLoading: movesLoading } = usePokemon(pokemon.id);
  const moves = fullPokemon?.moves ?? [];

  const pickedSet = new Set(currentMoveNames.filter(Boolean) as string[]);
  const groups = useMemo(() => groupMoves(moves), [moves]);

  const filteredGroups = useMemo(() => {
    if (!search) return groups;
    const q = search.toLowerCase();
    const result: Partial<Record<LearnMethod, MoveEntry[]>> = {};
    for (const [method, entries] of Object.entries(groups) as [LearnMethod, MoveEntry[]][]) {
      const matches = entries.filter((e) => formatPokemonName(e.name).toLowerCase().includes(q));
      if (matches.length > 0) result[method] = matches;
    }
    return result as Record<LearnMethod, MoveEntry[]>;
  }, [groups, search]);

  const toggleGroup = (method: LearnMethod) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      next.has(method) ? next.delete(method) : next.add(method);
      return next;
    });
  };

  const totalMoves = moves.length;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-5 w-full max-w-xl bg-bg-surface border border-bg-border rounded-2xl overflow-hidden shadow-2xl flex flex-col h-[88vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-bg-border shrink-0">
          <div>
            <h2
              className="text-sm font-bold text-text-primary tracking-widest"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              SELECT MOVE
            </h2>
            <p className="text-[10px] text-text-muted mt-0.5" style={{ fontFamily: "var(--font-jetbrains)" }}>
              {formatPokemonName(pokemon.name)} · {totalMoves} moves
            </p>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Search */}
        <div className="p-3 border-b border-bg-border shrink-0">
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              autoFocus
              type="text"
              placeholder="Search moves..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); if (e.target.value) setExpandedGroups(new Set<LearnMethod>(["level-up","machine","egg","tutor","other"])); }}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-8 pr-4 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 transition-colors"
            />
          </div>
        </div>

        {/* Dual-pane: list + preview */}
        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* Move list */}
          <div className="flex-1 overflow-y-auto">
            {movesLoading ? (
              <div className="p-4 space-y-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-8 rounded shimmer" />
                ))}
              </div>
            ) : (["level-up", "machine", "egg", "tutor", "other"] as LearnMethod[]).map((method) => {
              const entries = filteredGroups[method];
              if (!entries || entries.length === 0) return null;
              const expanded = expandedGroups.has(method) || !!search;

              return (
                <div key={method}>
                  <button
                    onClick={() => toggleGroup(method)}
                    className="w-full flex items-center justify-between px-4 py-2 border-b border-bg-border hover:bg-bg-elevated transition-colors"
                  >
                    <span
                      className="text-[9px] text-text-muted tracking-widest font-bold"
                      style={{ fontFamily: "var(--font-unbounded)" }}
                    >
                      {METHOD_LABELS[method]} ({entries.length})
                    </span>
                    {expanded ? <ChevronDown size={11} className="text-text-muted" /> : <ChevronRight size={11} className="text-text-muted" />}
                  </button>

                  {expanded && entries.map((entry) => {
                    const isPicked = pickedSet.has(entry.name);
                    const isHovered = hovered === entry.name;

                    return (
                      <button
                        key={entry.name}
                        disabled={isPicked}
                        onClick={() => { onSelect(entry.name); onClose(); }}
                        onMouseEnter={() => setHovered(entry.name)}
                        onMouseLeave={() => setHovered(null)}
                        className={`w-full text-left px-4 py-2 flex items-center justify-between transition-colors border-b border-bg-border/40 ${
                          isPicked
                            ? "opacity-30 cursor-not-allowed"
                            : isHovered
                            ? "bg-accent/10"
                            : "hover:bg-bg-elevated cursor-pointer"
                        }`}
                      >
                        <span className="text-xs text-text-primary">
                          {formatPokemonName(entry.name)}
                        </span>
                        {entry.method === "level-up" && entry.level > 0 && (
                          <span
                            className="text-[9px] text-text-muted"
                            style={{ fontFamily: "var(--font-jetbrains)" }}
                          >
                            Lv.{entry.level}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* Preview pane — always rendered at fixed width to prevent layout shift on hover */}
          <div className="w-52 shrink-0 border-l border-bg-border bg-bg-elevated overflow-hidden flex flex-col">
            <div className="p-3 border-b border-bg-border shrink-0">
              <p
                className="text-[9px] text-text-muted tracking-widest"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                PREVIEW
              </p>
            </div>
            {hovered ? (
              <MovePreviewPanel name={hovered} />
            ) : (
              <p className="text-[10px] text-text-muted p-3 leading-relaxed" style={{ fontFamily: "var(--font-jetbrains)" }}>
                Hover a move to preview details
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
