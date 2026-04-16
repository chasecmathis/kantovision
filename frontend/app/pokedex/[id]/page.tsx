"use client";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, ChevronLeft, ChevronRight, Star, Shield, Sword, Zap } from "lucide-react";
import { usePokemon, usePokemonSpecies, useEvolutionChain } from "@/src/hooks/usePokemon";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { StatBar } from "@/src/components/pokemon/StatBar";
import {
  getOfficialArtwork,
  formatPokemonName,
  getEnglishFlavorText,
  getEnglishGenus,
  flattenEvolutionChain,
} from "@/src/lib/pokeapi";
import { getTypeGradient, TYPE_COLORS } from "@/src/lib/typeColors";
import { getEffectiveness, ALL_TYPES } from "@/src/lib/typeChart";
import { padId } from "@/src/lib/utils";

function EffectivenessSection({ types }: { types: string[] }) {
  const grouped = {
    "4×": ALL_TYPES.filter((t) => getEffectiveness(t, types) === 4),
    "2×": ALL_TYPES.filter((t) => getEffectiveness(t, types) === 2),
    "½×": ALL_TYPES.filter((t) => getEffectiveness(t, types) === 0.5),
    "¼×": ALL_TYPES.filter((t) => getEffectiveness(t, types) === 0.25),
    "0×": ALL_TYPES.filter((t) => getEffectiveness(t, types) === 0),
  };

  return (
    <div className="space-y-3">
      {Object.entries(grouped)
        .filter(([, v]) => v.length > 0)
        .map(([label, types]) => (
          <div key={label} className="flex items-start gap-3">
            <span
              className={`text-xs font-bold w-7 shrink-0 pt-0.5 ${
                label.startsWith("4") ? "text-red-400" :
                label.startsWith("2") ? "text-orange-400" :
                label.startsWith("0×") ? "text-blue-400" :
                "text-green-400"
              }`}
              style={{ fontFamily: "var(--font-jetbrains)" }}
            >
              {label}
            </span>
            <div className="flex flex-wrap gap-1">
              {types.map((t) => (
                <TypeBadge key={t} type={t} size="sm" />
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const pokemonId = parseInt(id, 10);

  const pokemonQuery = usePokemon(pokemonId);
  const speciesQuery = usePokemonSpecies(pokemonId);
  const evolutionQuery = useEvolutionChain(speciesQuery.data?.evolution_chain.url);

  const pokemon = pokemonQuery.data;
  const species = speciesQuery.data;

  if (pokemonQuery.isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-12 animate-pulse">
        <div className="h-8 w-32 rounded shimmer mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="h-80 rounded-2xl shimmer" />
          <div className="space-y-4">
            <div className="h-10 w-48 rounded shimmer" />
            <div className="h-4 w-64 rounded shimmer" />
          </div>
        </div>
      </div>
    );
  }

  if (!pokemon) return null;

  const types = pokemon.types.map((t) => t.type.name);
  const gradient = getTypeGradient(types);
  const artwork = getOfficialArtwork(pokemon.id);
  const flavorText = species ? getEnglishFlavorText(species) : "";
  const genus = species ? getEnglishGenus(species) : "";
  const evolutions = evolutionQuery.data
    ? flattenEvolutionChain(evolutionQuery.data.chain)
    : [];

  const totalStats = pokemon.stats.reduce((s, st) => s + st.base_stat, 0);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Back + Nav */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors text-sm"
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <div className="flex items-center gap-2">
          {pokemonId > 1 && (
            <Link
              href={`/pokedex/${pokemonId - 1}`}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-bg-border bg-bg-surface hover:border-accent/30 text-text-secondary hover:text-text-primary transition-all text-sm"
            >
              <ChevronLeft size={14} />
              #{padId(pokemonId - 1)}
            </Link>
          )}
          <Link
            href={`/pokedex/${pokemonId + 1}`}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-bg-border bg-bg-surface hover:border-accent/30 text-text-secondary hover:text-text-primary transition-all text-sm"
          >
            #{padId(pokemonId + 1)}
            <ChevronRight size={14} />
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {/* Left — Artwork */}
        <div className="md:col-span-2">
          <div
            className="relative rounded-2xl border border-bg-border overflow-hidden p-8 flex items-center justify-center"
            style={{
              background: `linear-gradient(135deg, #0e0e1a 0%, #0e0e1a 50%), ${gradient}`,
              backgroundBlendMode: "normal",
            }}
          >
            <div
              className="absolute inset-0"
              style={{ background: gradient, opacity: 0.4 }}
            />
            {/* Decorative ring */}
            <div
              className="absolute inset-8 rounded-full border opacity-10"
              style={{ borderColor: TYPE_COLORS[types[0]] }}
            />
            <div
              className="absolute inset-16 rounded-full border opacity-5"
              style={{ borderColor: TYPE_COLORS[types[0]] }}
            />

            <div className="relative w-52 h-52">
              <Image
                src={artwork}
                alt={pokemon.name}
                fill
                className="object-contain drop-shadow-2xl"
                sizes="208px"
                unoptimized
                priority
              />
            </div>

            {/* Badges */}
            <div className="absolute top-3 right-3 flex flex-col gap-1 items-end">
              {species?.is_legendary && (
                <span className="flex items-center gap-1 text-yellow-400 text-xs border border-yellow-400/30 bg-yellow-400/10 px-2 py-0.5 rounded">
                  <Star size={10} /> Legendary
                </span>
              )}
              {species?.is_mythical && (
                <span className="flex items-center gap-1 text-purple-400 text-xs border border-purple-400/30 bg-purple-400/10 px-2 py-0.5 rounded">
                  <Zap size={10} /> Mythical
                </span>
              )}
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 gap-2 mt-3">
            {[
              { label: "Height", value: `${(pokemon.height / 10).toFixed(1)}m` },
              { label: "Weight", value: `${(pokemon.weight / 10).toFixed(1)}kg` },
              { label: "Base XP", value: pokemon.base_experience ?? "—" },
              { label: "BST", value: totalStats },
            ].map(({ label, value }) => (
              <div key={label} className="bg-bg-surface border border-bg-border rounded-lg px-3 py-2">
                <p className="text-text-muted text-[10px] tracking-wider" style={{ fontFamily: "var(--font-unbounded)" }}>
                  {label.toUpperCase()}
                </p>
                <p className="text-text-primary text-sm font-bold mt-0.5" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {value}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Info */}
        <div className="md:col-span-3 space-y-5">
          {/* Header */}
          <div>
            <p className="poke-id mb-1">#{padId(pokemon.id)}</p>
            <h1
              className="text-4xl font-black text-text-primary leading-none"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {formatPokemonName(pokemon.name).toUpperCase()}
            </h1>
            {genus && (
              <p className="text-text-secondary text-sm mt-1">{genus}</p>
            )}
            <div className="flex gap-2 mt-3">
              {types.map((t) => (
                <TypeBadge key={t} type={t} size="lg" />
              ))}
            </div>
          </div>

          {/* Flavor text */}
          {flavorText && (
            <p className="text-text-secondary text-sm leading-relaxed italic border-l-2 border-accent/30 pl-4">
              "{flavorText}"
            </p>
          )}

          {/* Abilities */}
          <div>
            <SectionTitle>Abilities</SectionTitle>
            <div className="flex gap-2 flex-wrap">
              {pokemon.abilities.map((a) => (
                <span
                  key={a.ability.name}
                  className={`px-3 py-1 rounded-lg text-sm border ${
                    a.is_hidden
                      ? "border-accent/30 bg-accent/10 text-accent"
                      : "border-bg-border bg-bg-surface text-text-primary"
                  }`}
                >
                  {formatPokemonName(a.ability.name)}
                  {a.is_hidden && (
                    <span className="text-xs text-text-muted ml-1">(hidden)</span>
                  )}
                </span>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div>
            <SectionTitle>Base Stats</SectionTitle>
            <div className="space-y-2">
              {pokemon.stats.map((s, i) => (
                <StatBar
                  key={s.stat.name}
                  name={s.stat.name}
                  value={s.base_stat}
                  delay={i * 20}
                />
              ))}
            </div>
          </div>

          {/* Type effectiveness */}
          <div>
            <SectionTitle icon={<Shield size={13} />}>Type Weaknesses</SectionTitle>
            <EffectivenessSection types={types} />
          </div>

          {/* Evolution */}
          {evolutions.length > 1 && (
            <div>
              <SectionTitle>Evolution Chain</SectionTitle>
              <div className="flex items-center gap-2 flex-wrap">
                {evolutions.map((evo, i) => (
                  <div key={evo.id} className="flex items-center gap-2">
                    {i > 0 && (
                      <ChevronRight size={14} className="text-text-muted" />
                    )}
                    <Link
                      href={`/pokedex/${evo.id}`}
                      className={`flex flex-col items-center gap-1 p-2 rounded-lg border transition-all ${
                        evo.id === pokemonId
                          ? "border-accent/40 bg-accent/10"
                          : "border-bg-border bg-bg-surface hover:border-accent/20"
                      }`}
                    >
                      <div className="w-14 h-14 relative">
                        <Image
                          src={getOfficialArtwork(evo.id)}
                          alt={evo.name}
                          fill
                          className="object-contain"
                          sizes="56px"
                          unoptimized
                        />
                      </div>
                      <span className="text-xs text-text-secondary capitalize">{evo.name}</span>
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children, icon }: { children: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      {icon && <span className="text-text-muted">{icon}</span>}
      <h3
        className="text-[10px] font-bold text-text-muted tracking-[0.25em] uppercase"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {children}
      </h3>
      <div className="flex-1 h-px bg-bg-border" />
    </div>
  );
}
