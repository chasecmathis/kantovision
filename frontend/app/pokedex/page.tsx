"use client";
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal, X, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchPokemonList, fetchPokemon, formatPokemonName, getPokemonId } from "@/src/lib/pokeapi";
import { PokemonCard, PokemonCardSkeleton } from "@/src/components/pokemon/PokemonCard";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { ALL_TYPES } from "@/src/lib/typeChart";
import { GEN_RANGES, POKEDEX_PAGE_SIZE, type GenRange } from "@/src/lib/constants";

export default function PokedexPage() {
  const [search, setSearch] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [genFilter, setGenFilter] = useState<GenRange>(GEN_RANGES[0]);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const pokemonQueries = useQuery({
    queryKey: ["pokemon-batch", genFilter.start, genFilter.count],
    queryFn: async () => {
      const list = await fetchPokemonList(genFilter.count, genFilter.start);
      const results = await Promise.all(
        list.map((p) => fetchPokemon(getPokemonId(p.url)))
      );
      return results;
    },
    staleTime: 1000 * 60 * 10,
  });

  const filtered = useMemo(() => {
    if (!pokemonQueries.data) return [];
    return pokemonQueries.data.filter((p) => {
      const nameMatch =
        !search ||
        formatPokemonName(p.name).toLowerCase().includes(search.toLowerCase()) ||
        String(p.id).includes(search);
      const typeMatch =
        selectedTypes.length === 0 ||
        selectedTypes.every((t) => p.types.some((pt) => pt.type.name === t));
      return nameMatch && typeMatch;
    });
  }, [pokemonQueries.data, search, selectedTypes]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / POKEDEX_PAGE_SIZE));
  const paginated = filtered.slice(
    (currentPage - 1) * POKEDEX_PAGE_SIZE,
    currentPage * POKEDEX_PAGE_SIZE
  );

  const handleGenChange = (gen: GenRange) => {
    setGenFilter(gen);
    setCurrentPage(1);
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setCurrentPage(1);
  };

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
    setCurrentPage(1);
  };

  const clearTypes = () => {
    setSelectedTypes([]);
    setCurrentPage(1);
  };

  const clearSearch = () => {
    setSearch("");
    setCurrentPage(1);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <p
          className="text-xs text-text-muted tracking-[0.3em] mb-2"
          style={{ fontFamily: "var(--font-jetbrains)" }}
        >
          // DATABASE
        </p>
        <h1
          className="text-3xl font-black text-text-primary tracking-tight"
          style={{ fontFamily: "var(--font-unbounded)" }}
        >
          POKÉDEX
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          {pokemonQueries.data?.length ?? "..."} entries · {filtered.length} shown
          {totalPages > 1 && (
            <span className="text-text-muted ml-1" style={{ fontFamily: "var(--font-jetbrains)" }}>
              · pg {currentPage}/{totalPages}
            </span>
          )}
        </p>
      </div>

      {/* Gen selector */}
      <div className="flex gap-2 flex-wrap mb-6">
        {GEN_RANGES.map((gen) => (
          <button
            key={gen.label}
            onClick={() => handleGenChange(gen)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all border ${
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

      {/* Search + Filter bar */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
          />
          <input
            type="text"
            placeholder="Search by name or number..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full bg-bg-surface border border-bg-border rounded-lg pl-9 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 transition-colors"
            style={{ fontFamily: "var(--font-dm-sans)" }}
          />
          {search && (
            <button
              onClick={clearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-all ${
            showFilters || selectedTypes.length > 0
              ? "bg-accent/20 border-accent/40 text-text-primary"
              : "bg-bg-surface border-bg-border text-text-secondary hover:border-accent/20"
          }`}
        >
          <SlidersHorizontal size={14} />
          {selectedTypes.length > 0 ? `${selectedTypes.length} types` : "Filter"}
        </button>
      </div>

      {/* Type filters */}
      {showFilters && (
        <div className="flex flex-wrap gap-2 mb-6 p-4 bg-bg-surface rounded-xl border border-bg-border animate-fade-in">
          {ALL_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => toggleType(type)}
              className={`transition-all rounded-md ${
                selectedTypes.includes(type) ? "ring-2 ring-white/20 scale-105" : "opacity-60 hover:opacity-100"
              }`}
            >
              <TypeBadge type={type} size="sm" />
            </button>
          ))}
          {selectedTypes.length > 0 && (
            <button
              onClick={clearTypes}
              className="text-xs text-text-muted hover:text-text-primary px-2"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {/* Grid */}
      {pokemonQueries.isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {Array.from({ length: POKEDEX_PAGE_SIZE }).map((_, i) => (
            <PokemonCardSkeleton key={i} />
          ))}
        </div>
      ) : pokemonQueries.isError ? (
        <div className="text-center py-20 text-text-secondary">
          <p className="text-4xl mb-4">⚠</p>
          <p>Failed to load Pokémon data.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-text-secondary">
          <p className="text-4xl mb-4">?</p>
          <p>No Pokémon found matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {paginated.map((pokemon, i) => (
            <PokemonCard key={pokemon.id} pokemon={pokemon} index={i} />
          ))}
        </div>
      )}

      {/* Pagination controls */}
      {!pokemonQueries.isLoading && !pokemonQueries.isError && totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-bg-border text-xs font-medium text-text-secondary hover:border-accent/30 hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            <ChevronLeft size={13} />
            PREV
          </button>

          <span
            className="text-xs text-text-muted tabular-nums px-2"
            style={{ fontFamily: "var(--font-jetbrains)" }}
          >
            {currentPage} / {totalPages}
          </span>

          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-bg-border text-xs font-medium text-text-secondary hover:border-accent/30 hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            NEXT
            <ChevronRight size={13} />
          </button>
        </div>
      )}
    </div>
  );
}
