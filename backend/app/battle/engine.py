from __future__ import annotations

import copy
import random
from dataclasses import dataclass

from app.battle.state import BattleState, MoveSlot, PlayerState, PokemonBattleState

# ─── Type effectiveness chart: TYPE_CHART[attacking][defending] = multiplier ──
# Missing entries default to 1.0 (neutral).
TYPE_CHART: dict[str, dict[str, float]] = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {
        "fire": 0.5,
        "water": 0.5,
        "rock": 0.5,
        "dragon": 0.5,
        "grass": 2.0,
        "ice": 2.0,
        "bug": 2.0,
        "steel": 2.0,
    },
    "water": {"water": 0.5, "grass": 0.5, "dragon": 0.5, "fire": 2.0, "ground": 2.0, "rock": 2.0},
    "electric": {
        "electric": 0.5,
        "grass": 0.5,
        "dragon": 0.5,
        "ground": 0.0,
        "water": 2.0,
        "flying": 2.0,
    },
    "grass": {
        "fire": 0.5,
        "grass": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "bug": 0.5,
        "dragon": 0.5,
        "steel": 0.5,
        "water": 2.0,
        "ground": 2.0,
        "rock": 2.0,
    },
    "ice": {
        "fire": 0.5,
        "water": 0.5,
        "ice": 0.5,
        "steel": 0.5,
        "grass": 2.0,
        "ground": 2.0,
        "flying": 2.0,
        "dragon": 2.0,
    },
    "fighting": {
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 0.5,
        "bug": 0.5,
        "fairy": 0.5,
        "ghost": 0.0,
        "normal": 2.0,
        "ice": 2.0,
        "rock": 2.0,
        "dark": 2.0,
        "steel": 2.0,
    },
    "poison": {
        "poison": 0.5,
        "ground": 0.5,
        "rock": 0.5,
        "ghost": 0.5,
        "steel": 0.0,
        "grass": 2.0,
        "fairy": 2.0,
    },
    "ground": {
        "grass": 0.5,
        "bug": 0.5,
        "flying": 0.0,
        "fire": 2.0,
        "electric": 2.0,
        "poison": 2.0,
        "rock": 2.0,
        "steel": 2.0,
    },
    "flying": {
        "electric": 0.5,
        "rock": 0.5,
        "steel": 0.5,
        "grass": 2.0,
        "fighting": 2.0,
        "bug": 2.0,
    },
    "psychic": {"psychic": 0.5, "steel": 0.5, "dark": 0.0, "fighting": 2.0, "poison": 2.0},
    "bug": {
        "fire": 0.5,
        "fighting": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "ghost": 0.5,
        "steel": 0.5,
        "fairy": 0.5,
        "grass": 2.0,
        "psychic": 2.0,
        "dark": 2.0,
    },
    "rock": {
        "fighting": 0.5,
        "ground": 0.5,
        "steel": 0.5,
        "fire": 2.0,
        "ice": 2.0,
        "flying": 2.0,
        "bug": 2.0,
    },
    "ghost": {"normal": 0.0, "dark": 0.5, "psychic": 2.0, "ghost": 2.0},
    "dragon": {"steel": 0.5, "fairy": 0.0, "dragon": 2.0},
    "dark": {"fighting": 0.5, "dark": 0.5, "fairy": 0.5, "psychic": 2.0, "ghost": 2.0},
    "steel": {
        "fire": 0.5,
        "water": 0.5,
        "electric": 0.5,
        "steel": 0.5,
        "ice": 2.0,
        "rock": 2.0,
        "fairy": 2.0,
    },
    "fairy": {
        "fire": 0.5,
        "poison": 0.5,
        "steel": 0.5,
        "fighting": 2.0,
        "dragon": 2.0,
        "dark": 2.0,
    },
}


def get_type_effectiveness(attacking: str, defending_types: list[str]) -> float:
    chart = TYPE_CHART.get(attacking, {})
    mult = 1.0
    for def_type in defending_types:
        mult *= chart.get(def_type, 1.0)
    return mult


def calc_damage(
    attacker: PokemonBattleState,
    defender: PokemonBattleState,
    move: MoveSlot,
) -> int:
    """Gen I-style damage formula at level 50."""
    if move.power == 0 or move.category == "status":
        return 0

    level = 50
    if move.category == "physical":
        atk = attacker.attack
        def_ = max(1, defender.defense)
    else:
        atk = attacker.special_attack
        def_ = max(1, defender.special_defense)

    base = (2 * level / 5 + 2) * move.power * atk / def_
    damage = int(base / 50 + 2)

    effectiveness = get_type_effectiveness(move.type, defender.types)
    damage = int(damage * effectiveness)

    # STAB (Same Type Attack Bonus)
    if move.type in attacker.types:
        damage = int(damage * 1.5)

    if effectiveness == 0:
        return 0
    return max(1, damage)


@dataclass
class TurnResult:
    new_state: BattleState
    log_entries: list[str]
    battle_over: bool
    winner_id: str | None


def _advance_active(player: PlayerState) -> None:
    """Move active_index to the next non-fainted Pokémon, if one exists."""
    for i, mon in enumerate(player.team):
        if not mon.fainted:
            player.active_index = i
            return


def resolve_turn(state: BattleState, move_p1: int, move_p2: int) -> TurnResult:
    """
    Execute one full turn. Returns a new BattleState with updated HP, log,
    and battle-over status. Pure function — does not mutate the input state.
    """
    new_state = copy.deepcopy(state)
    log: list[str] = []

    p1 = new_state.player1
    p2 = new_state.player2
    mon1 = p1.team[p1.active_index]
    mon2 = p2.team[p2.active_index]

    # Clamp move indices to valid range
    move_p1 = min(move_p1, max(0, len(mon1.moves) - 1))
    move_p2 = min(move_p2, max(0, len(mon2.moves) - 1))
    mv1 = mon1.moves[move_p1] if mon1.moves else None
    mv2 = mon2.moves[move_p2] if mon2.moves else None

    # Determine speed order; break ties randomly
    if mon1.speed > mon2.speed or (mon1.speed == mon2.speed and random.random() < 0.5):
        order = [(p1, mon1, mv1, p2, mon2), (p2, mon2, mv2, p1, mon1)]
    else:
        order = [(p2, mon2, mv2, p1, mon1), (p1, mon1, mv1, p2, mon2)]

    for att_player, attacker, move, def_player, defender in order:
        if attacker.fainted or move is None:
            continue

        effectiveness = get_type_effectiveness(move.type, defender.types)

        if effectiveness == 0:
            log.append(f"{attacker.name} used {move.name}! It had no effect on {defender.name}.")
            continue

        dmg = calc_damage(attacker, defender, move)
        defender.current_hp = max(0, defender.current_hp - dmg)

        eff_text = ""
        if effectiveness >= 2:
            eff_text = " It's super effective!"
        elif 0 < effectiveness < 1:
            eff_text = " It's not very effective..."

        log.append(f"{attacker.name} used {move.name}!{eff_text} ({dmg} damage)")

        if defender.current_hp == 0:
            defender.fainted = True
            log.append(f"{defender.name} fainted!")
            _advance_active(def_player)

    # Determine battle outcome
    p1_alive = any(not m.fainted for m in p1.team)
    p2_alive = any(not m.fainted for m in p2.team)

    battle_over = not p1_alive or not p2_alive
    winner_id: str | None = None

    if battle_over:
        if p1_alive:
            winner_id = p1.user_id
        elif p2_alive:
            winner_id = p2.user_id
        new_state.status = "ended"
        new_state.winner_id = winner_id

    new_state.turn += 1
    new_state.pending_moves.clear()
    new_state.log.extend(log)

    return TurnResult(
        new_state=new_state,
        log_entries=log,
        battle_over=battle_over,
        winner_id=winner_id,
    )
