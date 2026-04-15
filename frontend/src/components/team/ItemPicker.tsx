"use client";
import { useState } from "react";
import Image from "next/image";
import { Package, X } from "lucide-react";
import { useItem } from "@/src/hooks/usePokemon";
import { formatPokemonName } from "@/src/lib/pokeapi";
import { ItemPickerModal } from "./ItemPickerModal";

interface ItemPickerProps {
  selected: string | null;
  onChange: (name: string | null) => void;
}

function SelectedItemDisplay({ name, onClear }: { name: string; onClear: () => void }) {
  const { data, isLoading } = useItem(name);

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-bg-border bg-bg-elevated group">
      <div className="relative w-6 h-6 shrink-0">
        {data?.sprites.default ? (
          <Image
            src={data.sprites.default}
            alt={name}
            fill
            className="object-contain"
            sizes="24px"
            unoptimized
          />
        ) : (
          <Package size={14} className="text-text-muted absolute inset-0 m-auto" />
        )}
      </div>
      <span className="text-xs text-text-primary flex-1 truncate" style={{ fontFamily: "var(--font-dm-sans)" }}>
        {isLoading ? "Loading..." : data ? formatPokemonName(data.name) : formatPokemonName(name)}
      </span>
      <button
        onClick={(e) => { e.stopPropagation(); onClear(); }}
        className="text-text-muted hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
      >
        <X size={12} />
      </button>
    </div>
  );
}

export function ItemPicker({ selected, onChange }: ItemPickerProps) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      {selected ? (
        <div className="cursor-pointer" onClick={() => setModalOpen(true)}>
          <SelectedItemDisplay name={selected} onClear={() => onChange(null)} />
        </div>
      ) : (
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg border-2 border-dashed border-bg-border hover:border-accent/30 hover:bg-accent/5 transition-all w-full"
        >
          <Package size={13} className="text-text-muted" />
          <span className="text-xs text-text-muted">No item held</span>
        </button>
      )}
      {modalOpen && (
        <ItemPickerModal
          onSelect={(name) => { onChange(name); setModalOpen(false); }}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}
