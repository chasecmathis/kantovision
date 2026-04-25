from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.repositories import ability_repo, item_repo, move_repo, nature_repo, pokemon_repo

router = APIRouter(tags=["pokedex"])


# ─── Response models ──────────────────────────────────────────────────────────

class TypeSlotOut(BaseModel):
    slot: int
    name: str


class AbilitySlotOut(BaseModel):
    name: str
    is_hidden: bool


class StatsOut(BaseModel):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


class SpritesOut(BaseModel):
    front_default: str | None
    official_artwork: str | None
    shiny: str | None
    home: str | None


class MoveEntryOut(BaseModel):
    name: str
    method: str
    level: int | None = None


class EvolutionEntryOut(BaseModel):
    id: int
    name: str


class PokemonDetailOut(BaseModel):
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
    evolution_chain: list[EvolutionEntryOut]
    types: list[TypeSlotOut]
    abilities: list[AbilitySlotOut]
    stats: StatsOut
    sprites: SpritesOut
    moves: list[MoveEntryOut]


class PokemonListItemOut(BaseModel):
    id: int
    name: str
    generation: int
    types: list[TypeSlotOut]
    sprite_official_artwork: str | None


class MoveOut(BaseModel):
    id: int
    name: str
    power: int | None
    accuracy: int | None
    pp: int
    type: str
    damage_class: str
    flavor_text: str | None


class AbilityOut(BaseModel):
    name: str
    short_effect: str | None
    effect: str | None


class NatureOut(BaseModel):
    name: str
    increased_stat: str | None
    decreased_stat: str | None


class ItemListItemOut(BaseModel):
    id: int
    name: str
    sprite_url: str | None
    category: str | None


class ItemDetailOut(BaseModel):
    id: int
    name: str
    sprite_url: str | None
    category: str | None
    flavor_text: str | None


class EvolutionChainOut(BaseModel):
    id: int
    chain: list[EvolutionEntryOut]


# ─── Pokémon endpoints ────────────────────────────────────────────────────────

@router.get("/pokemon", response_model=list[PokemonListItemOut])
def list_pokemon(
    limit: int = Query(default=24, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    generation: int | None = Query(default=None, ge=1, le=9),
    types: str | None = Query(
        default=None, description="Comma-separated type names, e.g. fire,water"
    ),
) -> list[PokemonListItemOut]:
    type_list = [t.strip() for t in types.split(",")] if types else None
    rows = pokemon_repo.get_pokemon_list(
        get_db(),
        limit=limit,
        offset=offset,
        generation=generation,
        types=type_list,
    )
    return [
        PokemonListItemOut(
            id=r.id,
            name=r.name,
            generation=r.generation,
            types=[TypeSlotOut(slot=t.slot, name=t.name) for t in r.types],
            sprite_official_artwork=r.sprite_official_artwork,
        )
        for r in rows
    ]


@router.get("/pokemon/{pokemon_id}", response_model=PokemonDetailOut)
def get_pokemon(pokemon_id: int) -> PokemonDetailOut:
    db = get_db()
    detail = pokemon_repo.get_pokemon(db, pokemon_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Pokémon {pokemon_id} not found")
    return _detail_to_out(detail)


@router.get("/evolution-chains/{chain_id}", response_model=EvolutionChainOut)
def get_evolution_chain(chain_id: int) -> EvolutionChainOut:
    entries = pokemon_repo.get_evolution_chain(get_db(), chain_id)
    if entries is None:
        raise HTTPException(status_code=404, detail=f"Evolution chain {chain_id} not found")
    return EvolutionChainOut(
        id=chain_id,
        chain=[EvolutionEntryOut(id=e.id, name=e.name) for e in entries],
    )


# ─── Move endpoints ───────────────────────────────────────────────────────────

@router.get("/moves/{name}", response_model=MoveOut)
def get_move(name: str) -> MoveOut:
    row = move_repo.get_move(get_db(), name)
    if not row:
        raise HTTPException(status_code=404, detail=f"Move '{name}' not found")
    return MoveOut(
        id=row.id,
        name=row.name,
        power=row.power,
        accuracy=row.accuracy,
        pp=row.pp,
        type=row.type,
        damage_class=row.damage_class,
        flavor_text=row.flavor_text,
    )


# ─── Ability endpoints ────────────────────────────────────────────────────────

@router.get("/abilities/{name}", response_model=AbilityOut)
def get_ability(name: str) -> AbilityOut:
    row = ability_repo.get_ability(get_db(), name)
    if not row:
        raise HTTPException(status_code=404, detail=f"Ability '{name}' not found")
    return AbilityOut(name=row.name, short_effect=row.short_effect, effect=row.effect)


# ─── Nature endpoints ─────────────────────────────────────────────────────────

@router.get("/natures", response_model=list[NatureOut])
def list_natures() -> list[NatureOut]:
    rows = nature_repo.get_all_natures(get_db())
    return [
        NatureOut(name=r.name, increased_stat=r.increased_stat, decreased_stat=r.decreased_stat)
        for r in rows
    ]


# ─── Item endpoints ───────────────────────────────────────────────────────────

@router.get("/items", response_model=list[ItemListItemOut])
def list_items(
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
) -> list[ItemListItemOut]:
    rows = item_repo.get_item_list(get_db(), limit=limit, offset=offset, search=search)
    return [
        ItemListItemOut(id=r.id, name=r.name, sprite_url=r.sprite_url, category=r.category)
        for r in rows
    ]


@router.get("/items/{name}", response_model=ItemDetailOut)
def get_item(name: str) -> ItemDetailOut:
    row = item_repo.get_item(get_db(), name)
    if not row:
        raise HTTPException(status_code=404, detail=f"Item '{name}' not found")
    return ItemDetailOut(
        id=row.id, name=row.name, sprite_url=row.sprite_url,
        category=row.category, flavor_text=row.flavor_text,
    )


# ─── Private helpers ──────────────────────────────────────────────────────────

def _detail_to_out(d: pokemon_repo.PokemonDetail) -> PokemonDetailOut:
    return PokemonDetailOut(
        id=d.id,
        name=d.name,
        generation=d.generation,
        height=d.height,
        weight=d.weight,
        base_experience=d.base_experience,
        is_legendary=d.is_legendary,
        is_mythical=d.is_mythical,
        color=d.color,
        capture_rate=d.capture_rate,
        base_happiness=d.base_happiness,
        flavor_text=d.flavor_text,
        genus=d.genus,
        evolution_chain_id=d.evolution_chain_id,
        evolution_chain=[EvolutionEntryOut(id=e.id, name=e.name) for e in d.evolution_chain],
        types=[TypeSlotOut(slot=t.slot, name=t.name) for t in d.types],
        abilities=[AbilitySlotOut(name=a.name, is_hidden=a.is_hidden) for a in d.abilities],
        stats=StatsOut(
            hp=d.stats.hp,
            attack=d.stats.attack,
            defense=d.stats.defense,
            special_attack=d.stats.special_attack,
            special_defense=d.stats.special_defense,
            speed=d.stats.speed,
        ),
        sprites=SpritesOut(
            front_default=d.sprites.front_default,
            official_artwork=d.sprites.official_artwork,
            shiny=d.sprites.shiny,
            home=d.sprites.home,
        ),
        moves=[MoveEntryOut(name=m.name, method=m.method, level=m.level) for m in d.moves],
    )
