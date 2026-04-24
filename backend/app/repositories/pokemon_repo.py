from __future__ import annotations

from dataclasses import dataclass, field

from supabase import Client

_POKEMON_DETAIL_SELECT = (
    "id, name, generation, height, weight, base_experience, "
    "hp, attack, defense, special_attack, special_defense, speed, "
    "is_legendary, is_mythical, color, capture_rate, base_happiness, "
    "flavor_text, genus, evolution_chain_id, "
    "sprite_front, sprite_official_artwork, sprite_shiny, sprite_home, "
    "pokemon_types(type_name, slot), "
    "pokemon_abilities(ability_name, is_hidden, slot), "
    "evolution_chains(chain), "
    "pokemon_learnable_moves(learn_method, min_level, moves(name))"
)

_POKEMON_LIST_SELECT = (
    "id, name, generation, "
    "sprite_official_artwork, "
    "pokemon_types(type_name, slot)"
)


@dataclass
class TypeSlot:
    slot: int
    name: str


@dataclass
class AbilitySlot:
    name: str
    is_hidden: bool


@dataclass
class Stats:
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


@dataclass
class Sprites:
    front_default: str | None
    official_artwork: str | None
    shiny: str | None
    home: str | None


@dataclass
class MoveEntry:
    name: str
    method: str
    level: int | None = None


@dataclass
class EvolutionEntry:
    id: int
    name: str


@dataclass
class PokemonDetail:
    id: int
    name: str
    generation: int
    height: int | None
    weight: int | None
    base_experience: int | None
    is_legendary: bool
    is_mythical: bool
    color: str | None
    capture_rate: int | None
    base_happiness: int | None
    flavor_text: str | None
    genus: str | None
    evolution_chain_id: int | None
    evolution_chain: list[EvolutionEntry]
    types: list[TypeSlot]
    abilities: list[AbilitySlot]
    stats: Stats
    sprites: Sprites
    moves: list[MoveEntry] = field(default_factory=list)


@dataclass
class PokemonListRow:
    id: int
    name: str
    generation: int
    types: list[TypeSlot]
    sprite_official_artwork: str | None


def _parse_detail(d: dict) -> PokemonDetail:
    evo_data = d.get("evolution_chains") or {}
    raw_chain = evo_data.get("chain") or [] if evo_data else []

    move_entries: list[MoveEntry] = []
    for lm in d.get("pokemon_learnable_moves") or []:
        move_info = lm.get("moves") or {}
        move_name = move_info.get("name")
        if move_name:
            move_entries.append(
                MoveEntry(
                    name=move_name,
                    method=lm["learn_method"],
                    level=lm.get("min_level"),
                )
            )

    return PokemonDetail(
        id=d["id"],
        name=d["name"],
        generation=d["generation"],
        height=d.get("height"),
        weight=d.get("weight"),
        base_experience=d.get("base_experience"),
        is_legendary=d.get("is_legendary") or False,
        is_mythical=d.get("is_mythical") or False,
        color=d.get("color"),
        capture_rate=d.get("capture_rate"),
        base_happiness=d.get("base_happiness"),
        flavor_text=d.get("flavor_text"),
        genus=d.get("genus"),
        evolution_chain_id=d.get("evolution_chain_id"),
        evolution_chain=[EvolutionEntry(**e) for e in raw_chain],
        types=sorted(
            [TypeSlot(slot=t["slot"], name=t["type_name"]) for t in (d.get("pokemon_types") or [])],
            key=lambda t: t.slot,
        ),
        abilities=sorted(
            [
                AbilitySlot(name=a["ability_name"], is_hidden=a["is_hidden"])
                for a in (d.get("pokemon_abilities") or [])
            ],
            key=lambda a: a.name,
        ),
        stats=Stats(
            hp=d["hp"],
            attack=d["attack"],
            defense=d["defense"],
            special_attack=d["special_attack"],
            special_defense=d["special_defense"],
            speed=d["speed"],
        ),
        sprites=Sprites(
            front_default=d.get("sprite_front"),
            official_artwork=d.get("sprite_official_artwork"),
            shiny=d.get("sprite_shiny"),
            home=d.get("sprite_home"),
        ),
        moves=move_entries,
    )


def get_pokemon(db: Client, pokemon_id: int) -> PokemonDetail | None:
    result = (
        db.table("pokemon")
        .select(_POKEMON_DETAIL_SELECT)
        .eq("id", pokemon_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return _parse_detail(result.data)


def get_pokemon_list(
    db: Client,
    *,
    limit: int = 24,
    offset: int = 0,
    generation: int | None = None,
    types: list[str] | None = None,
) -> list[PokemonListRow]:
    """Return a paginated list of Pokémon, optionally filtered by generation and/or types."""

    # If filtering by types, collect the intersection of pokemon_ids for each type
    filtered_ids: set[int] | None = None
    if types:
        for type_name in types:
            res = (
                db.table("pokemon_types")
                .select("pokemon_id")
                .eq("type_name", type_name)
                .execute()
            )
            ids = {r["pokemon_id"] for r in (res.data or [])}
            filtered_ids = ids if filtered_ids is None else filtered_ids & ids
        if not filtered_ids:
            return []

    query = db.table("pokemon").select(_POKEMON_LIST_SELECT)

    if generation is not None:
        query = query.eq("generation", generation)

    if filtered_ids is not None:
        query = query.in_("id", list(filtered_ids))

    result = query.order("id").range(offset, offset + limit - 1).execute()

    rows = []
    for d in (result.data or []):
        rows.append(
            PokemonListRow(
                id=d["id"],
                name=d["name"],
                generation=d["generation"],
                sprite_official_artwork=d.get("sprite_official_artwork"),
                types=sorted(
                    [TypeSlot(slot=t["slot"], name=t["type_name"]) for t in (d.get("pokemon_types") or [])],
                    key=lambda t: t.slot,
                ),
            )
        )
    return rows


def get_evolution_chain(db: Client, chain_id: int) -> list[EvolutionEntry] | None:
    result = (
        db.table("evolution_chains")
        .select("chain")
        .eq("id", chain_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return [EvolutionEntry(**e) for e in (result.data.get("chain") or [])]
