"use client";
import { useState, useRef, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import { Upload, Scan, Cpu, Zap, RotateCcw, ExternalLink } from "lucide-react";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { StatBar } from "@/src/components/pokemon/StatBar";
import { usePokemon } from "@/src/hooks/usePokemon";
import {
  formatPokemonName,
  getOfficialArtwork,
} from "@/src/lib/pokeapi";
import { getTypeGradient } from "@/src/lib/typeColors";
import { padId } from "@/src/lib/utils";

// Mock classifier — in production, replace with actual TF.js model inference
const MOCK_PREDICTIONS = [
  { name: "charizard", confidence: 0.91 },
  { name: "pikachu", confidence: 0.94 },
  { name: "mewtwo", confidence: 0.88 },
  { name: "gengar", confidence: 0.85 },
  { name: "snorlax", confidence: 0.79 },
  { name: "eevee", confidence: 0.96 },
  { name: "bulbasaur", confidence: 0.82 },
  { name: "squirtle", confidence: 0.87 },
];

async function mockClassify(file: File): Promise<{ name: string; confidence: number }[]> {
  // Simulate inference delay
  await new Promise((r) => setTimeout(r, 1800));
  const top = MOCK_PREDICTIONS[Math.floor(Math.random() * MOCK_PREDICTIONS.length)];
  // Generate fake top-5 candidates
  const others = MOCK_PREDICTIONS
    .filter((p) => p.name !== top.name)
    .slice(0, 4)
    .map((p) => ({ ...p, confidence: p.confidence * (0.3 + Math.random() * 0.4) }));
  return [top, ...others].sort((a, b) => b.confidence - a.confidence);
}

type ScanState = "idle" | "scanning" | "done";

function ResultCard({ name, confidence }: { name: string; confidence: number }) {
  const pokemonQuery = usePokemon(name);
  const pokemon = pokemonQuery.data;

  if (!pokemon) return null;

  const types = pokemon.types.map((t) => t.type.name);
  const gradient = getTypeGradient(types);
  const genus = pokemon.genus ?? "";
  const flavorText = pokemon.flavor_text ?? "";

  return (
    <div className="animate-fade-up">
      <div
        className="relative rounded-2xl border border-bg-border overflow-hidden"
        style={{ background: "#0e0e1a" }}
      >
        {/* Background gradient */}
        <div className="absolute inset-0 opacity-30" style={{ background: gradient }} />

        <div className="relative p-6">
          <div className="flex gap-6">
            {/* Artwork */}
            <div className="shrink-0">
              <div
                className="relative w-32 h-32 rounded-xl overflow-hidden border border-bg-border"
                style={{ background: gradient }}
              >
                <Image
                  src={getOfficialArtwork(pokemon.id)}
                  alt={pokemon.name}
                  fill
                  className="object-contain p-2 drop-shadow-lg"
                  sizes="128px"
                  unoptimized
                />
              </div>
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="poke-id">#{padId(pokemon.id)}</p>
              <h2
                className="text-2xl font-black text-text-primary mt-1 leading-none"
                style={{ fontFamily: "var(--font-unbounded)" }}
              >
                {formatPokemonName(pokemon.name).toUpperCase()}
              </h2>
              {genus && (
                <p className="text-text-secondary text-xs mt-1">{genus}</p>
              )}
              <div className="flex gap-2 mt-2">
                {types.map((t) => (
                  <TypeBadge key={t} type={t} size="md" />
                ))}
              </div>

              {/* Confidence */}
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-text-muted" style={{ fontFamily: "var(--font-unbounded)" }}>
                    CONFIDENCE
                  </span>
                  <span
                    className={`font-bold ${confidence >= 0.85 ? "text-green-400" : confidence >= 0.6 ? "text-yellow-400" : "text-orange-400"}`}
                    style={{ fontFamily: "var(--font-jetbrains)" }}
                  >
                    {(confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${
                      confidence >= 0.85 ? "bg-green-400" : confidence >= 0.6 ? "bg-yellow-400" : "bg-orange-400"
                    }`}
                    style={{ width: `${confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Flavor text */}
          {flavorText && (
            <p className="mt-4 text-text-secondary text-sm leading-relaxed italic border-l-2 border-accent/30 pl-4">
              "{flavorText}"
            </p>
          )}

          {/* Stats */}
          <div className="mt-5 space-y-2">
            {pokemon.stats.slice(0, 6).map((s, i) => (
              <StatBar
                key={s.stat.name}
                name={s.stat.name}
                value={s.base_stat}
                delay={200 + i * 20}
              />
            ))}
          </div>

          {/* Link to detail */}
          <div className="mt-5">
            <Link
              href={`/pokedex/${pokemon.id}`}
              className="inline-flex items-center gap-2 text-xs text-accent hover:text-accent/80 border border-accent/30 hover:border-accent/50 px-4 py-2 rounded-lg transition-all"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              VIEW FULL ENTRY
              <ExternalLink size={11} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ScanPage() {
  const [state, setState] = useState<ScanState>("idle");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<{ name: string; confidence: number }[]>([]);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    setState("scanning");
    setPredictions([]);

    try {
      const results = await mockClassify(file);
      setPredictions(results);
      setState("done");
    } catch {
      setState("idle");
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) processFile(file);
    },
    [processFile]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const reset = () => {
    setState("idle");
    setImageUrl(null);
    setPredictions([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <p className="text-xs text-text-muted tracking-[0.3em] mb-2" style={{ fontFamily: "var(--font-jetbrains)" }}>
          // AI CLASSIFIER
        </p>
        <h1 className="text-3xl font-black text-text-primary tracking-tight" style={{ fontFamily: "var(--font-unbounded)" }}>
          AI SCANNER
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          Upload an image to identify the Pokémon using machine learning
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload zone */}
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />

          {imageUrl ? (
            <div className="relative rounded-2xl overflow-hidden border border-bg-border bg-bg-surface">
              <div className="relative aspect-square">
                <Image
                  src={imageUrl}
                  alt="Uploaded"
                  fill
                  className="object-contain"
                  unoptimized
                />
                {state === "scanning" && (
                  <div className="absolute inset-0 bg-bg-base/80 flex flex-col items-center justify-center gap-4">
                    {/* Scanning animation */}
                    <div className="relative w-24 h-24">
                      <div className="absolute inset-0 rounded-full border-2 border-accent/30 animate-ping" />
                      <div className="absolute inset-2 rounded-full border-2 border-accent/50 animate-ping" style={{ animationDelay: "200ms" }} />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Cpu size={32} className="text-accent animate-pulse" />
                      </div>
                    </div>
                    <p
                      className="text-xs text-accent tracking-widest"
                      style={{ fontFamily: "var(--font-unbounded)" }}
                    >
                      ANALYZING...
                    </p>
                    <div className="w-48 h-1 bg-bg-elevated rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full animate-[shimmer_1s_linear_infinite]" style={{ width: "60%" }} />
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 flex items-center justify-between border-t border-bg-border">
                <span className="text-xs text-text-muted" style={{ fontFamily: "var(--font-jetbrains)" }}>
                  {state === "scanning" ? "PROCESSING..." : state === "done" ? "CLASSIFICATION COMPLETE" : ""}
                </span>
                <button
                  onClick={reset}
                  className="flex items-center gap-2 text-xs text-text-secondary hover:text-text-primary transition-colors"
                  style={{ fontFamily: "var(--font-unbounded)" }}
                >
                  <RotateCcw size={12} />
                  RESET
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              className={`w-full aspect-square rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center gap-6 ${
                dragging
                  ? "border-accent bg-accent/10 scale-[0.99]"
                  : "border-bg-border hover:border-accent/40 hover:bg-accent/5"
              }`}
            >
              {/* Decorative rings */}
              <div className="relative">
                <div className="absolute -inset-8 rounded-full border border-accent/10" />
                <div className="absolute -inset-4 rounded-full border border-accent/15" />
                <div className="w-20 h-20 rounded-full border-2 border-accent/30 flex items-center justify-center bg-bg-surface">
                  <Upload size={28} className={`transition-colors ${dragging ? "text-accent" : "text-text-muted"}`} strokeWidth={1.5} />
                </div>
              </div>

              <div className="text-center">
                <p
                  className="text-sm font-bold text-text-primary"
                  style={{ fontFamily: "var(--font-unbounded)" }}
                >
                  UPLOAD IMAGE
                </p>
                <p className="text-xs text-text-muted mt-1">Drag & drop or click to select</p>
                <p className="text-xs text-text-muted mt-0.5">PNG, JPG, WEBP supported</p>
              </div>

              <div className="flex items-center gap-3 text-text-muted text-xs">
                <Scan size={12} />
                <span style={{ fontFamily: "var(--font-jetbrains)" }}>Powered by TF.js ViT model</span>
                <Zap size={12} />
              </div>
            </button>
          )}

          {/* Model info card */}
          <div className="mt-3 p-4 rounded-xl bg-bg-surface border border-bg-border">
            <div className="flex items-center gap-2 mb-2">
              <Cpu size={13} className="text-accent" />
              <span className="text-xs font-bold text-text-primary" style={{ fontFamily: "var(--font-unbounded)" }}>
                MODEL INFO
              </span>
            </div>
            <div className="space-y-1">
              {[
                ["Architecture", "ViT-Base (Vision Transformer)"],
                ["Training", "imjeffhi/pokemon_classifier"],
                ["Classes", "898 Pokémon species"],
                ["Input", "224×224 px · ImageNet norm"],
                ["Status", "Demo mode (mock inference)"],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs">
                  <span className="text-text-muted">{k}</span>
                  <span className="text-text-secondary" style={{ fontFamily: "var(--font-jetbrains)", fontSize: 10 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Results panel */}
        <div>
          {state === "idle" && (
            <div className="h-full min-h-64 flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-bg-border text-text-muted">
              <Scan size={32} strokeWidth={1} />
              <div className="text-center">
                <p className="text-sm font-medium text-text-secondary">Awaiting image</p>
                <p className="text-xs mt-1">Results will appear here after scanning</p>
              </div>
            </div>
          )}

          {state === "scanning" && (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-24 rounded-xl shimmer" style={{ opacity: 1 - i * 0.25 }} />
              ))}
            </div>
          )}

          {state === "done" && predictions.length > 0 && (
            <div className="space-y-4">
              {/* Top result */}
              <ResultCard name={predictions[0].name} confidence={predictions[0].confidence} />

              {/* Other candidates */}
              {predictions.length > 1 && (
                <div>
                  <p
                    className="text-[10px] text-text-muted tracking-widest mb-2"
                    style={{ fontFamily: "var(--font-unbounded)" }}
                  >
                    OTHER CANDIDATES
                  </p>
                  <div className="space-y-1.5">
                    {predictions.slice(1).map((pred) => (
                      <div
                        key={pred.name}
                        className="flex items-center gap-3 p-2.5 rounded-lg bg-bg-surface border border-bg-border"
                      >
                        <span className="text-xs text-text-secondary capitalize flex-1" style={{ fontFamily: "var(--font-dm-sans)" }}>
                          {formatPokemonName(pred.name)}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1 bg-bg-elevated rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-accent/50"
                              style={{ width: `${pred.confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-text-muted w-10 text-right" style={{ fontFamily: "var(--font-jetbrains)" }}>
                            {(pred.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
