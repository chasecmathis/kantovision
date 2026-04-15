"use client";
import { useState, useMemo } from "react";
import Image from "next/image";
import { Search, X } from "lucide-react";
import { useItemList, useItem } from "@/src/hooks/usePokemon";
import { formatPokemonName, getEnglishItemText } from "@/src/lib/pokeapi";

interface ItemPickerModalProps {
  onSelect: (name: string) => void;
  onClose: () => void;
}

function ItemPreview({ name }: { name: string }) {
  const { data, isLoading } = useItem(name);

  return (
    <div className="flex items-start gap-3 p-3 border-t border-bg-border bg-bg-elevated min-h-[60px]">
      {isLoading ? (
        <div className="h-4 w-full rounded shimmer" />
      ) : data ? (
        <>
          {data.sprites.default && (
            <div className="relative w-8 h-8 shrink-0">
              <Image
                src={data.sprites.default}
                alt={data.name}
                fill
                className="object-contain"
                sizes="32px"
                unoptimized
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-text-primary">{formatPokemonName(data.name)}</p>
            <p className="text-[10px] text-text-secondary mt-0.5 leading-relaxed line-clamp-2">
              {getEnglishItemText(data) || "No description available."}
            </p>
          </div>
        </>
      ) : null}
    </div>
  );
}

export function ItemPickerModal({ onSelect, onClose }: ItemPickerModalProps) {
  const [search, setSearch] = useState("");
  const [hovered, setHovered] = useState<string | null>(null);

  const { data: itemList, isLoading } = useItemList();

  const filtered = useMemo(() => {
    if (!itemList) return [];
    if (!search) return itemList;
    return itemList.filter((i) =>
      formatPokemonName(i.name).toLowerCase().includes(search.toLowerCase())
    );
  }, [itemList, search]);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 w-full max-w-md bg-bg-surface border border-bg-border rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-bg-border shrink-0">
          <h2
            className="text-sm font-bold text-text-primary tracking-widest"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            SELECT ITEM
          </h2>
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
              placeholder="Search items..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-8 pr-4 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 transition-colors"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {isLoading ? (
            <div className="p-4 space-y-1.5">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-8 rounded shimmer" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-8 text-text-secondary text-xs">No items found.</div>
          ) : (
            <div className="p-2">
              {filtered.slice(0, 100).map((item) => (
                <button
                  key={item.name}
                  onMouseEnter={() => setHovered(item.name)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => { onSelect(item.name); onClose(); }}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-bg-elevated transition-colors flex items-center gap-2 group"
                >
                  <span className="text-xs text-text-primary group-hover:text-white transition-colors">
                    {formatPokemonName(item.name)}
                  </span>
                </button>
              ))}
              {filtered.length > 100 && (
                <p className="text-center text-[10px] text-text-muted py-2">
                  Showing 100 of {filtered.length} — refine your search
                </p>
              )}
            </div>
          )}
        </div>

        {/* Item preview footer — always rendered at fixed height to prevent layout shift on hover */}
        <div className="shrink-0 border-t border-bg-border bg-bg-elevated min-h-[68px] flex items-center">
          {hovered ? (
            <ItemPreview name={hovered} />
          ) : (
            <p className="text-[10px] text-text-muted px-4" style={{ fontFamily: "var(--font-jetbrains)" }}>
              Hover an item to preview
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
