const BACKEND_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Interfaces (kept for backward compatibility with components) ─────────────

export interface PokemonListItem {
  name: string;
  url: string;
}

export interface PokemonType {
  slot: number;
  type: { name: string; url: string };
}

export interface PokemonStat {
  base_stat: number;
  stat: { name: string };
}

export interface PokemonMove {
  move: { name: string };
  version_group_details: { level_learned_at: number; move_learn_method: { name: string } }[];
}

export interface PokemonAbility {
  ability: { name: string };
  is_hidden: boolean;
}

export interface Pokemon {
  id: number;
  name: string;
  types: PokemonType[];
  stats: PokemonStat[];
  moves: PokemonMove[];
  abilities: PokemonAbility[];
  height: number;
  weight: number;
  base_experience: number;
  sprites: {
    front_default: string;
    other: {
      "official-artwork": { front_default: string; front_shiny: string };
      home: { front_default: string };
    };
  };
  // Species fields — included from backend so a separate fetchPokemonSpecies call is not needed
  is_legendary: boolean;
  is_mythical: boolean;
  flavor_text: string | null;
  genus: string | null;
  evolution_chain: { id: number; name: string }[];
}

export interface PokemonSpecies {
  id: number;
  name: string;
  flavor_text_entries: { flavor_text: string; language: { name: string }; version: { name: string } }[];
  genera: { genus: string; language: { name: string } }[];
  evolution_chain: { url: string };
  color: { name: string };
  is_legendary: boolean;
  is_mythical: boolean;
  base_happiness: number;
  capture_rate: number;
}

export interface EvolutionChain {
  chain: ChainLink;
}

export interface ChainLink {
  species: { name: string; url: string };
  evolves_to: ChainLink[];
  evolution_details: { min_level?: number; item?: { name: string }; trigger: { name: string } }[];
}

export interface MoveDetail {
  id: number;
  name: string;
  power: number | null;
  accuracy: number | null;
  pp: number;
  type: { name: string };
  damage_class: { name: string };
  flavor_text_entries: { flavor_text: string; language: { name: string } }[];
}

export interface Nature {
  name: string;
  increased_stat: { name: string } | null;
  decreased_stat: { name: string } | null;
}

export interface ItemListItem {
  name: string;
  url: string;
}

export interface ItemDetail {
  id: number;
  name: string;
  sprites: { default: string | null };
  flavor_text_entries: { text: string; language: { name: string } }[];
  attributes: { name: string }[];
  category: { name: string };
}

export interface AbilityDetail {
  name: string;
  effect_entries: { effect: string; short_effect: string; language: { name: string } }[];
}

export interface BaseStats {
  hp: number;
  attack: number;
  defense: number;
  "special-attack": number;
  "special-defense": number;
  speed: number;
}

export interface EVSpread {
  hp: number;
  attack: number;
  defense: number;
  "special-attack": number;
  "special-defense": number;
  speed: number;
}

export interface IVSpread {
  hp: number;
  attack: number;
  defense: number;
  "special-attack": number;
  "special-defense": number;
  speed: number;
}

export interface TeamMember {
  pokemon: Pokemon;
  abilityName: string;
  natureName: string | null;
  itemName: string | null;
  moveNames: (string | null)[];
  evs: EVSpread;
  ivs: IVSpread;
}

export type Team = (TeamMember | null)[];

// ─── Backend response types (internal) ───────────────────────────────────────

interface _BackendPokemon {
  id: number;
  name: string;
  generation: number;
  height: number | null;
  weight: number | null;
  base_experience: number | null;
  is_legendary: boolean;
  is_mythical: boolean;
  color: string | null;
  capture_rate: number | null;
  base_happiness: number | null;
  flavor_text: string | null;
  genus: string | null;
  evolution_chain_id: number | null;
  evolution_chain: { id: number; name: string }[];
  types: { slot: number; name: string }[];
  abilities: { name: string; is_hidden: boolean }[];
  stats: {
    hp: number;
    attack: number;
    defense: number;
    special_attack: number;
    special_defense: number;
    speed: number;
  };
  sprites: {
    front_default: string | null;
    official_artwork: string | null;
    shiny: string | null;
    home: string | null;
  };
  moves: { name: string; method: string; level: number | null }[];
}

// ─── Transformation helpers ───────────────────────────────────────────────────

function _toPokemon(d: _BackendPokemon): Pokemon {
  // Group moves by (name, method) so each move name appears once per method
  const moveMap = new Map<string, PokemonMove>();
  for (const m of d.moves) {
    const key = m.name;
    if (!moveMap.has(key)) {
      moveMap.set(key, {
        move: { name: m.name },
        version_group_details: [],
      });
    }
    moveMap.get(key)!.version_group_details.push({
      level_learned_at: m.level ?? 0,
      move_learn_method: { name: m.method },
    });
  }

  return {
    id: d.id,
    name: d.name,
    height: d.height ?? 0,
    weight: d.weight ?? 0,
    base_experience: d.base_experience ?? 0,
    types: d.types.map((t) => ({
      slot: t.slot,
      type: { name: t.name, url: "" },
    })),
    stats: [
      { base_stat: d.stats.hp, stat: { name: "hp" } },
      { base_stat: d.stats.attack, stat: { name: "attack" } },
      { base_stat: d.stats.defense, stat: { name: "defense" } },
      { base_stat: d.stats.special_attack, stat: { name: "special-attack" } },
      { base_stat: d.stats.special_defense, stat: { name: "special-defense" } },
      { base_stat: d.stats.speed, stat: { name: "speed" } },
    ],
    abilities: d.abilities.map((a) => ({
      ability: { name: a.name },
      is_hidden: a.is_hidden,
    })),
    sprites: {
      front_default: d.sprites.front_default ?? "",
      other: {
        "official-artwork": {
          front_default: d.sprites.official_artwork ?? "",
          front_shiny: d.sprites.shiny ?? "",
        },
        home: { front_default: d.sprites.home ?? "" },
      },
    },
    moves: Array.from(moveMap.values()),
    is_legendary: d.is_legendary,
    is_mythical: d.is_mythical,
    flavor_text: d.flavor_text,
    genus: d.genus,
    evolution_chain: d.evolution_chain,
  };
}

function _toSpecies(d: _BackendPokemon): PokemonSpecies {
  return {
    id: d.id,
    name: d.name,
    is_legendary: d.is_legendary,
    is_mythical: d.is_mythical,
    base_happiness: d.base_happiness ?? 0,
    capture_rate: d.capture_rate ?? 0,
    color: { name: d.color ?? "unknown" },
    // Single synthetic entry so getEnglishFlavorText() works without change
    flavor_text_entries: d.flavor_text
      ? [{ flavor_text: d.flavor_text, language: { name: "en" }, version: { name: "latest" } }]
      : [],
    genera: d.genus
      ? [{ genus: d.genus, language: { name: "en" } }]
      : [],
    // Point to our own evolution-chain endpoint so useEvolutionChain continues to work
    evolution_chain: {
      url: d.evolution_chain_id
        ? `${BACKEND_BASE}/evolution-chains/${d.evolution_chain_id}`
        : "",
    },
  };
}

function _buildChainLink(items: { id: number; name: string }[], idx: number): ChainLink {
  const item = items[idx];
  return {
    species: {
      name: item.name,
      // Use backend URL format so getPokemonId() (which takes last path segment) still works
      url: `${BACKEND_BASE}/pokemon/${item.id}`,
    },
    evolves_to: idx + 1 < items.length ? [_buildChainLink(items, idx + 1)] : [],
    evolution_details: [],
  };
}

// ─── Fetch functions ──────────────────────────────────────────────────────────

export async function fetchPokemonList(limit = 151, offset = 0): Promise<PokemonListItem[]> {
  const res = await fetch(`${BACKEND_BASE}/pokemon?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch pokemon list");
  const data: { id: number; name: string }[] = await res.json();
  return data.map((d) => ({
    name: d.name,
    // Encode the ID into a URL so getPokemonId() continues to work
    url: `${BACKEND_BASE}/pokemon/${d.id}`,
  }));
}

// Returns a full Pokemon[] suitable for PokemonCard in a single request.
// Uses the list endpoint which includes id, name, types, and sprite — no per-card fetch needed.
export async function fetchPokedexList(limit: number, offset: number): Promise<Pokemon[]> {
  const res = await fetch(`${BACKEND_BASE}/pokemon?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch pokedex list");
  const data: { id: number; name: string; generation: number; types: { slot: number; name: string }[]; sprite_official_artwork: string | null }[] = await res.json();
  return data.map((d) => ({
    id: d.id,
    name: d.name,
    height: 0,
    weight: 0,
    base_experience: 0,
    types: d.types.map((t) => ({ slot: t.slot, type: { name: t.name, url: "" } })),
    stats: [],
    abilities: [],
    moves: [],
    sprites: {
      front_default: "",
      other: {
        "official-artwork": { front_default: d.sprite_official_artwork ?? "", front_shiny: "" },
        home: { front_default: "" },
      },
    },
    is_legendary: false,
    is_mythical: false,
    flavor_text: null,
    genus: null,
    evolution_chain: [],
  }));
}

export async function fetchPokemon(nameOrId: string | number): Promise<Pokemon> {
  const res = await fetch(`${BACKEND_BASE}/pokemon/${nameOrId}`);
  if (!res.ok) throw new Error(`Failed to fetch pokemon: ${nameOrId}`);
  const data: _BackendPokemon = await res.json();
  return _toPokemon(data);
}

export async function fetchPokemonSpecies(nameOrId: string | number): Promise<PokemonSpecies> {
  const res = await fetch(`${BACKEND_BASE}/pokemon/${nameOrId}`);
  if (!res.ok) throw new Error(`Failed to fetch species: ${nameOrId}`);
  const data: _BackendPokemon = await res.json();
  return _toSpecies(data);
}

export async function fetchEvolutionChain(url: string): Promise<EvolutionChain> {
  if (!url) return { chain: { species: { name: "", url: "" }, evolves_to: [], evolution_details: [] } };
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch evolution chain");
  const data: { id: number; chain: { id: number; name: string }[] } = await res.json();
  if (!data.chain || data.chain.length === 0) {
    return { chain: { species: { name: "", url: "" }, evolves_to: [], evolution_details: [] } };
  }
  return { chain: _buildChainLink(data.chain, 0) };
}

export async function fetchMove(name: string): Promise<MoveDetail> {
  const res = await fetch(`${BACKEND_BASE}/moves/${name}`);
  if (!res.ok) throw new Error(`Failed to fetch move: ${name}`);
  const d = await res.json();
  return {
    id: d.id,
    name: d.name,
    power: d.power ?? null,
    accuracy: d.accuracy ?? null,
    pp: d.pp,
    type: { name: d.type },
    damage_class: { name: d.damage_class },
    // Single synthetic entry so getEnglishMoveText() works
    flavor_text_entries: d.flavor_text
      ? [{ flavor_text: d.flavor_text, language: { name: "en" } }]
      : [],
  };
}

export async function fetchNatureList(): Promise<Nature[]> {
  const res = await fetch(`${BACKEND_BASE}/natures`);
  if (!res.ok) throw new Error("Failed to fetch nature list");
  const data: { name: string; increased_stat: string | null; decreased_stat: string | null }[] =
    await res.json();
  return data.map((n) => ({
    name: n.name,
    increased_stat: n.increased_stat ? { name: n.increased_stat } : null,
    decreased_stat: n.decreased_stat ? { name: n.decreased_stat } : null,
  }));
}

export async function fetchItemList(limit = 200, offset = 0): Promise<ItemListItem[]> {
  const res = await fetch(`${BACKEND_BASE}/items?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch item list");
  const data: { id: number; name: string }[] = await res.json();
  return data.map((d) => ({
    name: d.name,
    url: `${BACKEND_BASE}/items/${d.name}`,
  }));
}

export async function fetchItem(name: string): Promise<ItemDetail> {
  const res = await fetch(`${BACKEND_BASE}/items/${name}`);
  if (!res.ok) throw new Error(`Failed to fetch item: ${name}`);
  const d = await res.json();
  return {
    id: d.id,
    name: d.name,
    sprites: { default: d.sprite_url ?? null },
    flavor_text_entries: d.flavor_text
      ? [{ text: d.flavor_text, language: { name: "en" } }]
      : [],
    attributes: [],
    category: { name: d.category ?? "unknown" },
  };
}

export async function fetchAbility(name: string): Promise<AbilityDetail> {
  const res = await fetch(`${BACKEND_BASE}/abilities/${name}`);
  if (!res.ok) throw new Error(`Failed to fetch ability: ${name}`);
  const d = await res.json();
  return {
    name: d.name,
    effect_entries: d.short_effect
      ? [{ effect: d.effect ?? "", short_effect: d.short_effect, language: { name: "en" } }]
      : [],
  };
}

// ─── Utilities (unchanged) ────────────────────────────────────────────────────

export function getPokemonId(url: string): number {
  const parts = url.split("/").filter(Boolean);
  return parseInt(parts[parts.length - 1], 10);
}

export function getOfficialArtwork(idOrSprites: number | Pokemon["sprites"]): string {
  if (typeof idOrSprites === "number") {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${idOrSprites}.png`;
  }
  return idOrSprites.other["official-artwork"].front_default;
}

export function getFrontDefault(idOrSprites: number | Pokemon["sprites"]): string {
  if (typeof idOrSprites === "number") {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${idOrSprites}.png`;
  }
  return idOrSprites.front_default;
}

export function formatStatName(stat: string): string {
  const map: Record<string, string> = {
    hp: "HP",
    attack: "ATK",
    defense: "DEF",
    "special-attack": "SpATK",
    "special-defense": "SpDEF",
    speed: "SPD",
  };
  return map[stat] ?? stat.toUpperCase();
}

export function formatPokemonName(name: string): string {
  return name
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function getEnglishFlavorText(species: PokemonSpecies): string {
  const entry = species.flavor_text_entries
    .filter((e) => e.language.name === "en")
    .pop();
  return entry?.flavor_text.replace(/\f/g, " ").replace(/\n/g, " ") ?? "";
}

export function getEnglishGenus(species: PokemonSpecies): string {
  return species.genera.find((g) => g.language.name === "en")?.genus ?? "";
}

export function flattenEvolutionChain(chain: ChainLink): { name: string; id: number }[] {
  const result: { name: string; id: number }[] = [];
  function walk(link: ChainLink) {
    const parts = link.species.url.split("/").filter(Boolean);
    const id = parseInt(parts[parts.length - 1], 10);
    result.push({ name: link.species.name, id });
    link.evolves_to.forEach(walk);
  }
  walk(chain);
  return result;
}

export function getEnglishAbilityEffect(ability: AbilityDetail): string {
  return ability.effect_entries.find((e) => e.language.name === "en")?.short_effect ?? "";
}

export function getEnglishItemText(item: ItemDetail): string {
  return (
    item.flavor_text_entries.find((e) => e.language.name === "en")?.text.replace(/\n/g, " ") ?? ""
  );
}

export function getEnglishMoveText(move: MoveDetail): string {
  return (
    move.flavor_text_entries
      .find((e) => e.language.name === "en")
      ?.flavor_text.replace(/\f/g, " ")
      .replace(/\n/g, " ") ?? ""
  );
}

export const STAT_DISPLAY: Record<string, string> = {
  hp: "HP",
  attack: "ATK",
  defense: "DEF",
  "special-attack": "SpATK",
  "special-defense": "SpDEF",
  speed: "SPD",
};

export const STAT_ORDER = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"] as const;

export function defaultEVs(): EVSpread {
  return { hp: 0, attack: 0, defense: 0, "special-attack": 0, "special-defense": 0, speed: 0 };
}

export function defaultIVs(): IVSpread {
  return { hp: 31, attack: 31, defense: 31, "special-attack": 31, "special-defense": 31, speed: 31 };
}

export function totalEVs(evs: EVSpread): number {
  return Object.values(evs).reduce((a, b) => a + b, 0);
}

export function createTeamMember(pokemon: Pokemon): TeamMember {
  return {
    pokemon,
    abilityName: pokemon.abilities[0]?.ability.name ?? "",
    natureName: null,
    itemName: null,
    moveNames: [null, null, null, null],
    evs: defaultEVs(),
    ivs: defaultIVs(),
  };
}
