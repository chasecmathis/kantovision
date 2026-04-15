"use client";
import Image from "next/image";
import { Plus, RotateCcw } from "lucide-react";
import { TypeBadge } from "@/src/components/pokemon/TypeBadge";
import { StatBar } from "@/src/components/pokemon/StatBar";
import { AbilitySelector } from "./AbilitySelector";
import { NatureSelector } from "./NatureSelector";
import { ItemPicker } from "./ItemPicker";
import { MoveSlots } from "./MoveSlots";
import { EVSliders } from "./EVSliders";
import { IVInputs } from "./IVInputs";
import {
  getOfficialArtwork,
  formatPokemonName,
  type TeamMember,
  getFrontDefault,
} from "@/src/lib/pokeapi";
import { getTypeGradient } from "@/src/lib/typeColors";
import { padId } from "@/src/lib/utils";

interface MemberEditorProps {
  member: TeamMember | null;
  slotIndex: number;
  onOpenPicker: () => void;
  onUpdate: (updater: (m: TeamMember) => TeamMember) => void;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-2.5">
      <h3
        className="text-[9px] font-bold text-text-muted tracking-[0.25em] uppercase"
        style={{ fontFamily: "var(--font-unbounded)" }}
      >
        {children}
      </h3>
      <div className="flex-1 h-px bg-bg-border" />
    </div>
  );
}

export function MemberEditor({ member, slotIndex, onOpenPicker, onUpdate }: MemberEditorProps) {
  if (!member) {
    return (
      <div className="h-full min-h-80 flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed border-bg-border bg-bg-surface/50 p-8">
        <button
          onClick={onOpenPicker}
          className="w-16 h-16 rounded-2xl border-2 border-dashed border-bg-border hover:border-accent/40 hover:bg-accent/5 flex items-center justify-center transition-all group"
        >
          <Plus size={22} className="text-text-muted group-hover:text-accent transition-colors" />
        </button>
        <div className="text-center">
          <p
            className="text-xs font-bold text-text-secondary"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            SLOT {slotIndex + 1}
          </p>
          <p className="text-[10px] text-text-muted mt-1">Click to add a Pokémon</p>
        </div>
      </div>
    );
  }

  const { pokemon, abilityName, natureName, itemName, moveNames, evs, ivs } = member;
  const types = pokemon.types.map((t) => t.type.name);
  const gradient = getTypeGradient(types);
  const bst = pokemon.stats.reduce((s, st) => s + st.base_stat, 0);

  return (
    <div className="bg-bg-surface border border-bg-border rounded-2xl overflow-hidden">
      {/* Identity header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-25" style={{ background: gradient }} />
        <div className="relative flex items-start gap-4 p-5">
          <div className="relative w-24 h-24 shrink-0">
            <Image
              src={getOfficialArtwork(pokemon.id)}
              alt={pokemon.name}
              fill
              className="object-contain drop-shadow-xl"
              sizes="96px"
              unoptimized
            />
          </div>
          <div className="flex-1 min-w-0 pt-1">
            <p className="poke-id">#{padId(pokemon.id)}</p>
            <h2
              className="text-xl font-black text-text-primary leading-tight mt-0.5"
              style={{ fontFamily: "var(--font-unbounded)" }}
            >
              {formatPokemonName(pokemon.name).toUpperCase()}
            </h2>
            <div className="flex gap-1.5 mt-2">
              {types.map((t) => <TypeBadge key={t} type={t} size="md" />)}
            </div>
            <p className="text-[10px] text-text-muted mt-1" style={{ fontFamily: "var(--font-jetbrains)" }}>
              BST {bst} · H{pokemon.height / 10}m · W{pokemon.weight / 10}kg
            </p>
          </div>
          <button
            onClick={onOpenPicker}
            className="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-bg-border bg-bg-elevated/80 text-[9px] text-text-muted hover:border-accent/30 hover:text-text-primary transition-all"
            style={{ fontFamily: "var(--font-unbounded)" }}
          >
            <RotateCcw size={10} />
            CHANGE
          </button>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Ability */}
        <div>
          <SectionTitle>Ability</SectionTitle>
          <AbilitySelector
            abilities={pokemon.abilities}
            selected={abilityName}
            onChange={(name) => onUpdate((m) => ({ ...m, abilityName: name }))}
          />
        </div>

        {/* Nature */}
        <div>
          <SectionTitle>Nature</SectionTitle>
          <NatureSelector
            selected={natureName}
            onChange={(name) => onUpdate((m) => ({ ...m, natureName: name }))}
          />
        </div>

        {/* Item */}
        <div>
          <SectionTitle>Held Item</SectionTitle>
          <ItemPicker
            selected={itemName}
            onChange={(name) => onUpdate((m) => ({ ...m, itemName: name }))}
          />
        </div>

        {/* Moves */}
        <div>
          <SectionTitle>Moves</SectionTitle>
          <MoveSlots
            pokemon={pokemon}
            moveNames={moveNames}
            onUpdate={(newMoveNames) => onUpdate((m) => ({ ...m, moveNames: newMoveNames }))}
          />
        </div>

        {/* EVs */}
        <div>
          <SectionTitle>Effort Values</SectionTitle>
          <EVSliders
            evs={evs}
            onChange={(newEvs) => onUpdate((m) => ({ ...m, evs: newEvs }))}
          />
        </div>

        {/* IVs */}
        <div>
          <SectionTitle>Individual Values</SectionTitle>
          <IVInputs
            ivs={ivs}
            onChange={(newIvs) => onUpdate((m) => ({ ...m, ivs: newIvs }))}
          />
        </div>

        {/* Base stats for reference */}
        <div>
          <SectionTitle>Base Stats</SectionTitle>
          <div className="space-y-1.5">
            {pokemon.stats.map((s, i) => (
              <StatBar key={s.stat.name} name={s.stat.name} value={s.base_stat} delay={i * 60} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
