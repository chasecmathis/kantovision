"use client";
import { useState, useMemo } from "react";
import Image from "next/image";
import { Search, X, SlidersHorizontal, ChevronLeft, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchPokemonList,
  fetchPokemon,
  formatPokemonName,
  getOfficialArtwork,
  getPokemonId,
  type Pokemon,
} from "@/src/lib/pokeapi";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { ALL_TYPES } from "@/src/lib/typeChart";
import { GEN_RANGES, MODAL_PAGE_SIZE, type GenRange } from "@/src/lib/constants";

import { type Team } from "@/src/lib/pokeapi";

interface PokemonPickerModalProps {
  onSelect: (pokemon: Pokemon) => void;
  onClose: () => void;
  currentTeam: Team;
}

export function PokemonPickerModal({ onSelect, onClose, currentTeam }: PokemonPickerModalProps) {
  const [search, setSearch] = useState("");
  const [genFilter, setGenFilter] = useState<GenRange>(GEN_RANGES[0]); // null = All gens
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [showTypePanel, setShowTypePanel] = useState(false);
  const [page, setPage] = useState(1);

  const { start, count } = genFilter ?? { start: 0, count: 1025 };

  const allPokemon = useQuery({
    queryKey: ["pokemon-batch", genFilter.start, genFilter.count],
    queryFn: async () => {
      const list = await fetchPokemonList(count, start);
      const results = await Promise.all(
        list.map((p) => fetchPokemon(getPokemonId(p.url)))
      );
      return results;
    },
    staleTime: 1000 * 60 * 30,
  });

  const teamIds = new Set(currentTeam.filter(Boolean).map((m) => m!.pokemon.id));

  const filtered = useMemo(() => {
    if (!allPokemon.data) return [];
    return allPokemon.data.filter((p) => {
      const nameMatch =
        !search ||
        formatPokemonName(p.name).toLowerCase().includes(search.toLowerCase()) ||
        String(p.id).includes(search);
      const typeMatch =
        !selectedType || p.types.some((pt) => pt.type.name === selectedType);
      return nameMatch && typeMatch;
    });
  }, [allPokemon.data, search, selectedType]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / MODAL_PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * MODAL_PAGE_SIZE, page * MODAL_PAGE_SIZE);

  const handleGenChange = (gen: GenRange) => {
    setGenFilter(gen);
    setPage(1);
  };

  const handleTypeChange = (type: string | null) => {
    setSelectedType(type);
    setPage(1);
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl bg-bg-surface border border-bg-border rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-bg-border shrink-0">
          <h2
            className="text-sm font-bold text-text-primary tracking-widest"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            SELECT POKÉMON
          </h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-bg-border shrink-0">
          <div className="relative">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
            />
            <input
              autoFocus
              type="text"
              placeholder="Search by name or number..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-9 pr-4 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 transition-colors"
            />
            {search && (
              <button
                onClick={() => handleSearchChange("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              >
                <X size={12} />
              </button>
            )}
          </div>
        </div>

        {/* Gen filter row */}
        <div className="px-4 py-3 border-b border-bg-border shrink-0 flex flex-wrap gap-1.5">
          {GEN_RANGES.map((gen) => (
            <button
              key={gen.label}
              onClick={() => handleGenChange(gen)}
              className={`px-2 py-1 rounded text-[10px] font-medium transition-all border ${
                genFilter.label === gen.label
                  ? "bg-accent/20 border-accent/40 text-text-primary"
                  : "border-bg-border text-text-secondary hover:border-accent/20 hover:text-text-primary"
              }`}
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {gen.label}
            </button>
          ))}
        </div>

        {/* Type filter toggle */}
        <div className="px-4 py-2.5 border-b border-bg-border shrink-0">
          <button
            onClick={() => setShowTypePanel((v) => !v)}
            className={`flex items-center gap-1.5 text-[10px] font-medium transition-all ${
              showTypePanel || selectedType
                ? "text-text-primary"
                : "text-text-secondary hover:text-text-primary"
            }`}
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            <SlidersHorizontal size={11} />
            TYPE
            {selectedType && (
              <span className="text-accent ml-1">· {selectedType.toUpperCase()}</span>
            )}
          </button>

          {showTypePanel && (
            <div className="flex flex-wrap gap-1 mt-2">
              {ALL_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() =>
                    handleTypeChange(selectedType === type ? null : type)
                  }
                  className={`transition-all rounded ${
                    selectedType === type
                      ? "ring-2 ring-white/20 scale-105"
                      : "opacity-60 hover:opacity-100"
                  }`}
                >
                  <TypeBadge type={type} size="sm" />
                </button>
              ))}
              {selectedType && (
                <button
                  onClick={() => handleTypeChange(null)}
                  className="text-[10px] text-text-muted hover:text-text-primary px-2"
                >
                  Clear
                </button>
              )}
            </div>
          )}
        </div>

        {/* Grid — scrollable */}
        <div className="flex-1 overflow-y-auto min-h-0 p-4">
          {allPokemon.isLoading ? (
            <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
              {Array.from({ length: MODAL_PAGE_SIZE }).map((_, i) => (
                <div key={i} className="h-24 rounded-lg shimmer" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-12 text-text-secondary text-xs">
              No Pokémon found.
            </div>
          ) : (
            <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
              {paginated.map((pokemon) => {
                const inTeam = teamIds.has(pokemon.id);
                const types = pokemon.types.map((t) => t.type.name);
                return (
                  <button
                    key={pokemon.id}
                    disabled={inTeam}
                    onClick={() => {
                      onSelect(pokemon);
                      onClose();
                    }}
                    className={`flex flex-col items-center gap-1 p-2 rounded-lg border transition-all ${
                      inTeam
                        ? "border-bg-border opacity-30 cursor-not-allowed"
                        : "border-bg-border bg-bg-elevated hover:border-accent/30 hover:bg-accent/5 cursor-pointer"
                    }`}
                  >
                    <div className="relative w-12 h-12">
                      <Image
                        src={getOfficialArtwork(pokemon.id)}
                        alt={pokemon.name}
                        fill
                        className="object-contain"
                        sizes="48px"
                        unoptimized
                      />
                    </div>
                    <p
                      className="text-[9px] text-text-secondary text-center leading-tight"
                      style={{ fontFamily: "var(--font-unbounded)" }}
                    >
                      {formatPokemonName(pokemon.name)}
                    </p>
                    <div className="flex gap-0.5 flex-wrap justify-center">
                      {types.map((t) => (
                        <TypeBadge key={t} type={t} size="sm" />
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Pagination footer */}
        {!allPokemon.isLoading && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-bg-border shrink-0">
            <span
              className="text-[10px] text-text-muted"
              style={{ fontFamily: "var(--font-jetbrains)" }}
            >
              {filtered.length} results
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 px-2.5 py-1 rounded border border-bg-border text-[10px] text-text-secondary hover:border-accent/30 hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                <ChevronLeft size={11} />
                PREV
              </button>
              <span
                className="text-[10px] text-text-muted tabular-nums w-12 text-center"
                style={{ fontFamily: "var(--font-jetbrains)" }}
              >
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex items-center gap-1 px-2.5 py-1 rounded border border-bg-border text-[10px] text-text-secondary hover:border-accent/30 hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                NEXT
                <ChevronRight size={11} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
