import { supabase } from "./supabase";
import type { Team, Pokemon, EVSpread, IVSpread, BaseStats } from "./pokeapi";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Serialization ───────────────────────────────────────────────────────────

export interface SerializedSlot {
  pokemon_id: number;
  species_name: string;
  types: string[];
  base_stats: {
    hp: number;
    attack: number;
    defense: number;
    special_attack: number;
    special_defense: number;
    speed: number;
  };
  ability: string;
  nature: string | null;
  item: string | null;
  move_names: (string | null)[];
  evs: {
    hp: number;
    attack: number;
    defense: number;
    special_attack: number;
    special_defense: number;
    speed: number;
  };
  ivs: {
    hp: number;
    attack: number;
    defense: number;
    special_attack: number;
    special_defense: number;
    speed: number;
  };
  // null = default form; "graveler-alola" = Alolan Graveler
  form_name: string | null;
}

export interface SavedTeam {
  id: string;
  name: string;
  slots: (SerializedSlot | null)[];
  created_at: string;
  updated_at: string;
}

/** Extract a typed BaseStats object from the raw PokéAPI stats array. */
function pokemonToBaseStats(pokemon: Pokemon): BaseStats {
  const map: Record<string, number> = Object.fromEntries(
    pokemon.stats.map((s) => [s.stat.name, s.base_stat])
  );
  return {
    hp: map["hp"] ?? 0,
    attack: map["attack"] ?? 0,
    defense: map["defense"] ?? 0,
    "special-attack": map["special-attack"] ?? 0,
    "special-defense": map["special-defense"] ?? 0,
    speed: map["speed"] ?? 0,
  };
}

function serializeBaseStats(baseStats: BaseStats) {
  return {
    hp: baseStats.hp,
    attack: baseStats.attack,
    defense: baseStats.defense,
    special_attack: baseStats["special-attack"],
    special_defense: baseStats["special-defense"],
    speed: baseStats.speed,
  };
}

function serializeEvs(evs: EVSpread) {
  return {
    hp: evs.hp,
    attack: evs.attack,
    defense: evs.defense,
    special_attack: evs["special-attack"],
    special_defense: evs["special-defense"],
    speed: evs.speed,
  };
}

function serializeIvs(ivs: IVSpread) {
  return {
    hp: ivs.hp,
    attack: ivs.attack,
    defense: ivs.defense,
    special_attack: ivs["special-attack"],
    special_defense: ivs["special-defense"],
    speed: ivs.speed,
  };
}

export function deserializeEvs(evs: SerializedSlot["evs"]): EVSpread {
  return {
    hp: evs.hp,
    attack: evs.attack,
    defense: evs.defense,
    "special-attack": evs.special_attack,
    "special-defense": evs.special_defense,
    speed: evs.speed,
  };
}

export function deserializeIvs(ivs: SerializedSlot["ivs"] | undefined): IVSpread {
  if (!ivs) return { hp: 31, attack: 31, defense: 31, "special-attack": 31, "special-defense": 31, speed: 31 };
  return {
    hp: ivs.hp,
    attack: ivs.attack,
    defense: ivs.defense,
    "special-attack": ivs.special_attack,
    "special-defense": ivs.special_defense,
    speed: ivs.speed,
  };
}

export function deserializeBaseStats(base_stats: SerializedSlot["base_stats"]): BaseStats {
  return {
    hp: base_stats.hp,
    attack: base_stats.attack,
    defense: base_stats.defense,
    "special-attack": base_stats.special_attack,
    "special-defense": base_stats.special_defense,
    speed: base_stats.speed,
  };
}

export function serializeTeam(team: Team): (SerializedSlot | null)[] {
  return team.map((m) => {
    if (!m) return null;
    return {
      pokemon_id: m.pokemon.id,
      species_name: m.pokemon.name,
      types: m.pokemon.types.map(t => t.type.name),
      base_stats: serializeBaseStats(pokemonToBaseStats(m.pokemon)),
      ability: m.abilityName,
      nature: m.natureName,
      item: m.itemName,
      move_names: m.moveNames,
      evs: serializeEvs(m.evs),
      ivs: serializeIvs(m.ivs),
      form_name: m.formName ?? null,
    };
  });
}

// ─── Auth header helper ──────────────────────────────────────────────────────

async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("Not authenticated");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await authHeaders();
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `API error ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─── Profile & Friend types ──────────────────────────────────────────────────

export interface ProfileData {
  id: string;
  username: string;
  display_name: string | null;
  created_at: string;
}

// ─── Team API ────────────────────────────────────────────────────────────────

export function fetchTeams(): Promise<SavedTeam[]> {
  return request<SavedTeam[]>("/teams");
}

export function createTeam(name: string, team: Team): Promise<SavedTeam> {
  return request<SavedTeam>("/teams", {
    method: "POST",
    body: JSON.stringify({ name, slots: serializeTeam(team) }),
  });
}

export function updateTeam(id: string, name: string, team: Team): Promise<SavedTeam> {
  return request<SavedTeam>(`/teams/${id}`, {
    method: "PUT",
    body: JSON.stringify({ name, slots: serializeTeam(team) }),
  });
}

export function deleteTeam(id: string): Promise<void> {
  return request<void>(`/teams/${id}`, { method: "DELETE" });
}

// ─── Profile API ─────────────────────────────────────────────────────────────

export async function getMyProfile(): Promise<ProfileData | null> {
  const headers = await authHeaders();
  const res = await fetch(`${API_URL}/profiles/me`, { headers });
  if (res.status === 404) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `API error ${res.status}`);
  }
  return res.json();
}

export function createProfile(username: string, displayName?: string | null): Promise<ProfileData> {
  return request<ProfileData>("/profiles", {
    method: "POST",
    body: JSON.stringify({ username, display_name: displayName ?? null }),
  });
}

export function updateProfile(displayName: string | null): Promise<ProfileData> {
  return request<ProfileData>("/profiles/me", {
    method: "PATCH",
    body: JSON.stringify({ display_name: displayName }),
  });
}

export function searchProfiles(username: string): Promise<ProfileData[]> {
  return request<ProfileData[]>(`/profiles?username=${encodeURIComponent(username)}`);
}

// ─── Battle API ───────────────────────────────────────────────────────────────

export interface BattleHistoryItem {
  id: string;
  player1_id: string;
  player2_id: string;
  player1_username: string | null;
  player2_username: string | null;
  winner_id: string | null;
  turns: number;
  created_at: string;
}

export function getBattleHistory(): Promise<BattleHistoryItem[]> {
  return request<BattleHistoryItem[]>("/battles/history");
}

export function fetchWsTicket(): Promise<{ ticket: string }> {
  return request<{ ticket: string }>("/ws/ticket", { method: "POST" });
}
