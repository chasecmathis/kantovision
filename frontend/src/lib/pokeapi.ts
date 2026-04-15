const BASE = "https://pokeapi.co/api/v2";

// ─── Existing interfaces ─────────────────────────────────────────────────────

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

// ─── New interfaces ──────────────────────────────────────────────────────────

export interface MoveDetail {
  id: number;
  name: string;
  power: number | null;
  accuracy: number | null;
  pp: number;
  type: { name: string };
  damage_class: { name: string }; // "physical" | "special" | "status"
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

// ─── Existing fetch functions ────────────────────────────────────────────────

export async function fetchPokemonList(limit = 151, offset = 0): Promise<PokemonListItem[]> {
  const res = await fetch(`${BASE}/pokemon?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch pokemon list");
  const data = await res.json();
  return data.results;
}

export async function fetchPokemon(nameOrId: string | number): Promise<Pokemon> {
  const res = await fetch(`${BASE}/pokemon/${nameOrId}`);
  if (!res.ok) throw new Error(`Failed to fetch pokemon: ${nameOrId}`);
  return res.json();
}

export async function fetchPokemonSpecies(nameOrId: string | number): Promise<PokemonSpecies> {
  const res = await fetch(`${BASE}/pokemon-species/${nameOrId}`);
  if (!res.ok) throw new Error(`Failed to fetch species: ${nameOrId}`);
  return res.json();
}

export async function fetchEvolutionChain(url: string): Promise<EvolutionChain> {
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch evolution chain");
  return res.json();
}

// ─── New fetch functions ─────────────────────────────────────────────────────

export async function fetchMove(name: string): Promise<MoveDetail> {
  const res = await fetch(`${BASE}/move/${name}`);
  if (!res.ok) throw new Error(`Failed to fetch move: ${name}`);
  return res.json();
}

export async function fetchNatureList(): Promise<Nature[]> {
  const listRes = await fetch(`${BASE}/nature?limit=25`);
  if (!listRes.ok) throw new Error("Failed to fetch nature list");
  const listData: { results: { name: string; url: string }[] } = await listRes.json();
  const natures = await Promise.all(
    listData.results.map(async (n) => {
      const r = await fetch(`${BASE}/nature/${n.name}`);
      if (!r.ok) throw new Error(`Failed to fetch nature: ${n.name}`);
      return r.json() as Promise<Nature>;
    })
  );
  return natures;
}

export async function fetchItemList(limit = 200, offset = 0): Promise<ItemListItem[]> {
  const res = await fetch(`${BASE}/item?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch item list");
  const data = await res.json();
  return data.results;
}

export async function fetchItem(name: string): Promise<ItemDetail> {
  const res = await fetch(`${BASE}/item/${name}`);
  if (!res.ok) throw new Error(`Failed to fetch item: ${name}`);
  return res.json();
}

export async function fetchAbility(name: string): Promise<AbilityDetail> {
  const res = await fetch(`${BASE}/ability/${name}`);
  if (!res.ok) throw new Error(`Failed to fetch ability: ${name}`);
  return res.json();
}

// ─── Utilities ───────────────────────────────────────────────────────────────

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
    move.flavor_text_entries.find((e) => e.language.name === "en")?.flavor_text.replace(/\f/g, " ").replace(/\n/g, " ") ?? ""
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
