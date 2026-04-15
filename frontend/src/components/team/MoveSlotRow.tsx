"use client";
import { Plus, X, Zap, Shield, Activity } from "lucide-react";
import { useMove } from "@/src/hooks/usePokemon";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { formatPokemonName } from "@/src/lib/pokeapi";

interface MoveSlotRowProps {
  moveName: string | null;
  slotIndex: number;
  onOpenPicker: () => void;
  onClear: () => void;
}

const CLASS_ICONS = {
  physical: <Zap size={10} />,
  special: <Activity size={10} />,
  status: <Shield size={10} />,
};

export function MoveSlotRow({ moveName, slotIndex, onOpenPicker, onClear }: MoveSlotRowProps) {
  const { data: move, isLoading } = useMove(moveName);

  if (!moveName) {
    return (
      <button
        onClick={onOpenPicker}
        className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg border-2 border-dashed border-bg-border hover:border-accent/30 hover:bg-accent/5 transition-all group"
      >
        <div className="w-5 h-5 rounded border border-bg-border flex items-center justify-center group-hover:border-accent/40 transition-colors">
          <Plus size={10} className="text-text-muted group-hover:text-accent" />
        </div>
        <span
          className="text-[10px] text-text-muted group-hover:text-text-secondary"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          MOVE {slotIndex + 1}
        </span>
      </button>
    );
  }

  if (isLoading) {
    return (
      <div className="px-3 py-2.5 rounded-lg border border-bg-border bg-bg-surface">
        <div className="h-3 w-32 rounded shimmer" />
      </div>
    );
  }

  const classIcon = move?.damage_class?.name
    ? CLASS_ICONS[move.damage_class.name as keyof typeof CLASS_ICONS]
    : null;

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-bg-border bg-bg-surface hover:border-accent/25 transition-all group">
      {move ? (
        <TypeBadge type={move.type.name} size="sm" />
      ) : (
        <div className="w-12 h-5 rounded shimmer shrink-0" />
      )}

      <span className="flex-1 text-xs text-text-primary min-w-0 truncate">
        {move ? formatPokemonName(move.name) : formatPokemonName(moveName)}
      </span>

      {move && (
        <div className="flex items-center gap-2 shrink-0">
          <span
            className="text-[9px] text-text-muted flex items-center gap-0.5"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {classIcon && <span className="text-text-muted">{classIcon}</span>}
            {move.power != null ? move.power : "—"}
          </span>
          <span
            className="text-[9px] text-text-muted"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {move.accuracy != null ? `${move.accuracy}%` : "—"}
          </span>
          <span
            className="text-[9px] text-text-muted"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            PP{move.pp}
          </span>
        </div>
      )}

      <button
        onClick={onClear}
        className="text-text-muted hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100 ml-1"
      >
        <X size={12} />
      </button>
    </div>
  );
}
