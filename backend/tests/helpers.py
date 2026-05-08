"""Shared test object factories."""

from app.battle.enums import StatusCondition, Terrain, Weather
from app.battle.matchmaking import QueueEntry
from app.battle.state import (
    BattleState,
    FieldState,
    MoveSlot,
    PlayerState,
    PokemonBattleState,
    StatStages,
)


def make_move(
    name: str = "tackle",
    power: int = 40,
    accuracy: int = 100,
    pp: int = 35,
    type_: str = "normal",
    category: str = "physical",
    priority: int = 0,
    effect_id: str = "",
    effect_chance: int = 0,
    flags: list[str] | None = None,
) -> MoveSlot:
    return MoveSlot(
        name=name,
        power=power,
        accuracy=accuracy,
        max_pp=pp,
        current_pp=pp,
        type=type_,
        category=category,
        priority=priority,
        effect_id=effect_id,
        effect_chance=effect_chance,
        flags=flags or [],
    )


def make_pokemon(
    name: str = "Bulbasaur",
    species_id: int = 1,
    hp: int = 100,
    attack: int = 49,
    defense: int = 49,
    special_attack: int = 65,
    special_defense: int = 65,
    speed: int = 45,
    types: list[str] | None = None,
    moves: list[MoveSlot] | None = None,
    fainted: bool = False,
    ability: str = "",
    item: str = "",
    nature: str = "",
    status: StatusCondition = StatusCondition.NONE,
    stat_stages: StatStages | None = None,
) -> PokemonBattleState:
    return PokemonBattleState(
        species_id=species_id,
        name=name,
        current_hp=hp if not fainted else 0,
        max_hp=hp,
        attack=attack,
        defense=defense,
        special_attack=special_attack,
        special_defense=special_defense,
        speed=speed,
        types=types if types is not None else ["normal"],
        moves=moves if moves is not None else [make_move()],
        fainted=fainted,
        ability=ability,
        item=item,
        nature=nature,
        status=status,
        stat_stages=stat_stages or StatStages(),
    )


def make_queue_entry(user_id: str = "user-1", team_id: str = "team-1") -> QueueEntry:
    return QueueEntry(user_id=user_id, team_id=team_id)


def make_battle_state(
    user1: str = "user-1",
    user2: str = "user-2",
    team1: list[PokemonBattleState] | None = None,
    team2: list[PokemonBattleState] | None = None,
    weather: Weather = Weather.NONE,
    weather_turns: int = 0,
    terrain: Terrain = Terrain.NONE,
    terrain_turns: int = 0,
) -> BattleState:
    return BattleState(
        id="battle-test-id",
        player1=PlayerState(user_id=user1, team=team1 or [make_pokemon(name="Mon1")]),
        player2=PlayerState(user_id=user2, team=team2 or [make_pokemon(name="Mon2")]),
        field=FieldState(
            weather=weather,
            weather_turns=weather_turns,
            terrain=terrain,
            terrain_turns=terrain_turns,
        ),
    )
