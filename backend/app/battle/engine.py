"""Battle engine — orchestrates the turn resolution pipeline."""

from __future__ import annotations

import copy
from random import Random

from pydantic import BaseModel, ConfigDict, Field

import app.battle.effects.abilities  # noqa: F401
import app.battle.effects.items  # noqa: F401

# Ensure effect data is registered on import
import app.battle.effects.moves  # noqa: F401
from app.battle.accuracy import accuracy_check
from app.battle.actions import Action, ActionType, MoveAction, SwitchAction
from app.battle.damage import calc_damage
from app.battle.effects.moves.effects import apply_move_effect, apply_status_move_effect
from app.battle.effects.moves.hazards import apply_switch_in_hazards
from app.battle.effects.registry import CUSTOM_MOVE_REGISTRY, MOVE_EFFECT_REGISTRY
from app.battle.enums import StatusCondition, Terrain, VolatileStatus, Weather
from app.battle.pipeline import Side, TurnContext
from app.battle.state import (
    STRUGGLE,
    BattleState,
    BattleStatus,
    MoveSlot,
    PlayerState,
    PokemonBattleState,
    StatStages,
)
from app.battle.status import apply_end_of_turn_damage, check_pre_turn, try_thaw_from_fire


class TurnResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    new_state: BattleState
    log_entries: list[str]
    battle_over: bool
    winner_id: str | None
    forced_switches: list[str] = Field(default_factory=list)


class ForcedSwitchResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    new_state: BattleState
    log_entries: list[str]
    needs_switch: bool = False
    battle_over: bool = False
    winner_id: str | None = None


class TurnEngine:
    """Orchestrates a single turn through the pipeline phases."""

    def __init__(self, rng: Random | None = None) -> None:
        self._rng = rng or Random()

    def resolve_turn(
        self,
        state: BattleState,
        action_p1: Action,
        action_p2: Action,
    ) -> TurnResult:
        """Execute one full turn. Pure function — does not mutate the input state."""
        ctx = TurnContext(copy.deepcopy(state), self._rng)

        # Clear Protect volatile from previous turn
        for side in ("p1", "p2"):
            mon = ctx.get_active(side)
            mon.volatile_statuses.discard(VolatileStatus.PROTECT)

        actions = self._order_actions(ctx, action_p1, action_p2)

        for action in actions:
            self._execute_action(ctx, action)

        # Reset protect_turns for Pokemon that didn't use Protect this turn
        for side in ("p1", "p2"):
            mon = ctx.get_active(side)
            if VolatileStatus.PROTECT not in mon.volatile_statuses:
                mon.volatile_data.pop("protect_turns", None)

        self._end_of_turn(ctx)
        self._check_battle_end(ctx)

        ctx.state.turn += 1
        ctx.state.pending_actions.clear()
        ctx.state.log.extend(ctx.log)

        return TurnResult(
            new_state=ctx.state,
            log_entries=ctx.log,
            battle_over=ctx.state.status == BattleStatus.ENDED,
            winner_id=ctx.state.winner_id,
            forced_switches=list(ctx.pending_forced_switches),
        )

    # ─── Action ordering ─────────────────────────────────────────────────

    def _order_actions(
        self,
        ctx: TurnContext,
        action_p1: Action,
        action_p2: Action,
    ) -> list[tuple[Side, Action]]:
        """Order actions: switches first, then by priority, then by speed."""
        entries: list[tuple[Side, Action, int, int]] = []
        for side, action in [("p1", action_p1), ("p2", action_p2)]:
            if action.type == ActionType.SWITCH:
                priority = 100
            elif isinstance(action, MoveAction):
                mon = ctx.get_active(side)
                move = self._resolve_move(mon, action.move_index)
                priority = move.priority
            else:
                priority = 0
            speed = ctx.get_effective_speed(ctx.get_active(side))
            entries.append((side, action, priority, speed))

        def sort_key(entry: tuple[Side, Action, int, int]) -> tuple[int, int, float]:
            _, _, prio, spd = entry
            return (-prio, -spd, self._rng.random())

        entries.sort(key=sort_key)
        return [(side, action) for side, action, _, _ in entries]

    # ─── Action execution ────────────────────────────────────────────────

    def _execute_action(self, ctx: TurnContext, entry: tuple[Side, Action]) -> None:
        side, action = entry
        if action.type == ActionType.MOVE and isinstance(action, MoveAction):
            self._execute_move(ctx, side, action)
        elif action.type == ActionType.SWITCH and isinstance(action, SwitchAction):
            self._execute_switch(ctx, side, action)

    def _resolve_move(self, mon: PokemonBattleState, move_index: int) -> MoveSlot:
        """Resolve which move to use, falling back to Struggle if all PP depleted."""
        if not mon.moves:
            return STRUGGLE
        if all(m.current_pp <= 0 for m in mon.moves):
            return STRUGGLE
        idx = min(move_index, len(mon.moves) - 1)
        move = mon.moves[idx]
        if move.current_pp <= 0:
            return STRUGGLE
        return move

    def _execute_move(self, ctx: TurnContext, side: Side, action: MoveAction) -> None:
        player = ctx.get_player(side)
        attacker = player.team[player.active_index]
        if attacker.fainted:
            return

        opp_side = ctx.get_opponent_side(side)
        opp_player = ctx.get_player(opp_side)
        defender = opp_player.team[opp_player.active_index]
        if defender.fainted:
            return

        # ── Flinch check (set by previous turn's move) ───────────────
        if VolatileStatus.FLINCH in attacker.volatile_statuses:
            ctx.log.append(f"{attacker.name} flinched and couldn't move!")
            attacker.volatile_statuses.discard(VolatileStatus.FLINCH)
            return

        # ── Pre-turn status check (sleep, freeze, paralysis) ─────────
        can_act, status_msg = check_pre_turn(attacker, self._rng)
        if status_msg:
            ctx.log.append(status_msg)
        if not can_act:
            return

        move = self._resolve_move(attacker, action.move_index)
        is_struggle = move is STRUGGLE

        # Deduct PP (Struggle doesn't cost PP)
        if not is_struggle:
            idx = min(action.move_index, len(attacker.moves) - 1)
            attacker.moves[idx].current_pp = max(0, attacker.moves[idx].current_pp - 1)

        # Look up move effect spec
        effect_spec = MOVE_EFFECT_REGISTRY.get(move.name)

        # ── Status moves (no damage) ─────────────────────────────────
        if move.category == "status" and not move.power:
            ctx.log.append(f"{attacker.name} used {move.name}!")
            # Custom handlers (hazards, protect, etc.)
            custom_handler = CUSTOM_MOVE_REGISTRY.get(move.name)
            if custom_handler:
                custom_handler(ctx, attacker, defender, self._rng)
            elif effect_spec:
                apply_status_move_effect(ctx, effect_spec, attacker, defender, self._rng)
            attacker.last_move_used = move.name
            return

        # ── Protect check ────────────────────────────────────────────
        if VolatileStatus.PROTECT in defender.volatile_statuses:
            ctx.log.append(f"{attacker.name} used {move.name}! {defender.name} protected itself!")
            attacker.last_move_used = move.name
            return

        # ── Defender's ability: on_try_hit (type immunities) ─────────
        def_ability = ctx.get_ability(defender)
        if def_ability and not is_struggle:
            if not def_ability.on_try_hit(ctx, attacker, defender, move):
                attacker.last_move_used = move.name
                return

        # ── Accuracy check ───────────────────────────────────────────
        if not accuracy_check(attacker, defender, move, self._rng):
            ctx.log.append(f"{attacker.name} used {move.name}! But it missed!")
            attacker.last_move_used = move.name
            return

        # ── Damage calculation ───────────────────────────────────────
        atk_ability = ctx.get_ability(attacker)
        atk_item = ctx.get_item(attacker)
        def_item = ctx.get_item(defender)
        result = calc_damage(
            attacker,
            defender,
            move,
            self._rng,
            weather=ctx.state.field.weather,
            atk_ability=atk_ability,
            atk_item=atk_item,
            def_item=def_item,
        )

        if result.effectiveness == 0:
            ctx.log.append(
                f"{attacker.name} used {move.name}! It had no effect on {defender.name}."
            )
            attacker.last_move_used = move.name
            return

        # ── Ability damage modifiers ─────────────────────────────────
        final_damage = result.damage
        if atk_ability:
            final_damage = atk_ability.on_modify_damage(
                ctx,
                attacker,
                defender,
                move,
                final_damage,
            )
        if def_ability:
            final_damage = def_ability.on_modify_damage(
                ctx,
                attacker,
                defender,
                move,
                final_damage,
            )

        # ── Item damage modifiers (Life Orb) ─────────────────────────
        if atk_item:
            final_damage = atk_item.on_modify_damage(
                ctx,
                attacker,
                defender,
                move,
                final_damage,
            )

        # ── Defender: on_before_faint — ability (Sturdy) + item (Focus Sash) ─
        if final_damage >= defender.current_hp:
            if def_ability:
                final_damage = def_ability.on_before_faint(ctx, defender, final_damage)
            if def_item and final_damage >= defender.current_hp:
                final_damage = def_item.on_before_faint(ctx, defender, final_damage)

        final_damage = max(1, final_damage)
        damage_dealt = ctx.apply_damage(defender, final_damage)

        # Build log entry
        parts = [f"{attacker.name} used {move.name}!"]
        if result.is_crit:
            parts.append("A critical hit!")
        if result.effectiveness >= 2:
            parts.append("It's super effective!")
        elif 0 < result.effectiveness < 1:
            parts.append("It's not very effective...")
        parts.append(f"({final_damage} damage)")
        ctx.log.append(" ".join(parts))

        # ── Fire-type move thaws frozen defender ─────────────────────
        if move.type == "fire" and not defender.fainted:
            thaw_msg = try_thaw_from_fire(defender, move.type)
            if thaw_msg:
                ctx.log.append(thaw_msg)

        # ── Move secondary effects ───────────────────────────────────
        if effect_spec and not is_struggle:
            apply_move_effect(ctx, effect_spec, attacker, defender, damage_dealt, self._rng)

        # ── Custom post-damage handler (Rapid Spin hazard clear) ─────
        custom_handler = CUSTOM_MOVE_REGISTRY.get(move.name)
        if custom_handler and not is_struggle:
            custom_handler(ctx, attacker, defender, self._rng)

        # ── Defender's ability: on_after_damage (contact abilities) ───
        if def_ability and not defender.fainted and not is_struggle:
            def_ability.on_after_damage(ctx, attacker, defender, move, damage_dealt)

        # ── Defender's item: on_after_damage (Rocky Helmet) ──────────
        if def_item and not defender.fainted and not is_struggle:
            def_item.on_after_damage(ctx, attacker, defender, move, damage_dealt)

        # ── Attacker's item: on_attacker_after_damage (Life Orb) ─────
        if atk_item and not is_struggle:
            atk_item.on_attacker_after_damage(ctx, attacker, defender, move, damage_dealt)

        # ── Struggle recoil ──────────────────────────────────────────
        if is_struggle:
            recoil = max(1, attacker.max_hp // 4)
            ctx.apply_damage(attacker, recoil)
            ctx.log.append(f"{attacker.name} is damaged by recoil!")

        attacker.last_move_used = move.name

        # ── Faint checks ─────────────────────────────────────────────
        if defender.fainted:
            ctx.log.append(f"{defender.name} fainted!")
            self._handle_faint(ctx, opp_player)

        if attacker.fainted:
            ctx.log.append(f"{attacker.name} fainted!")
            self._handle_faint(ctx, player)

    def _execute_switch(self, ctx: TurnContext, side: Side, action: SwitchAction) -> None:
        player = ctx.get_player(side)
        target_idx = action.switch_to_index
        if target_idx < 0 or target_idx >= len(player.team):
            return
        if player.team[target_idx].fainted:
            return
        if target_idx == player.active_index:
            return

        old_active = player.team[player.active_index]

        # ── Switch-out ability hook (Natural Cure, Regenerator) ────────
        old_ability = ctx.get_ability(old_active)
        if old_ability:
            old_ability.on_switch_out(ctx, old_active, side)

        # ── Switch-out: clear volatile statuses and reset stat stages ──
        old_active.volatile_statuses.clear()
        old_active.volatile_data.clear()
        old_active.stat_stages = StatStages()
        old_active.last_move_used = None
        # Reset toxic counter on switch-out (resets to base poison if re-sent out)
        if old_active.status == StatusCondition.TOXIC:
            old_active.status_turns = 0

        player.active_index = target_idx
        new_active = player.team[player.active_index]
        ctx.log.append(f"{old_active.name} was withdrawn! Go, {new_active.name}!")

        # ── Switch-in hazard damage ────────────────────────────────────
        apply_switch_in_hazards(ctx, new_active, side, self._rng)
        if new_active.fainted:
            self._handle_faint(ctx, player)
            return

        # ── Switch-in ability hook (Intimidate, weather setters) ───────
        new_ability = ctx.get_ability(new_active)
        if new_ability:
            new_ability.on_switch_in(ctx, new_active, side)

    # ─── End of turn ─────────────────────────────────────────────────────

    def _end_of_turn(self, ctx: TurnContext) -> None:
        """Apply end-of-turn effects: weather, terrain, status damage."""
        if ctx.state.status == BattleStatus.ENDED:
            return

        # ── Weather damage ──────────────────────────────────────────
        self._apply_weather_effects(ctx)

        # ── Terrain effects ─────────────────────────────────────────
        self._apply_terrain_effects(ctx)

        # ── Status damage (burn, poison, toxic) ─────────────────────
        for side in ("p1", "p2"):
            player = ctx.get_player(side)
            pokemon = player.team[player.active_index]
            if pokemon.fainted:
                continue

            dmg, msg = apply_end_of_turn_damage(pokemon)
            if msg:
                ctx.log.append(msg)

            if pokemon.fainted:
                ctx.log.append(f"{pokemon.name} fainted!")
                self._handle_faint(ctx, player)
                continue

            # Berry trigger after status/weather damage (Sitrus, Lum)
            item = ctx.get_item(pokemon)
            if item:
                item.on_after_status_damage(ctx, pokemon)

        # ── End-of-turn ability hooks (Speed Boost, etc.) ──────────
        for side in ("p1", "p2"):
            pokemon = ctx.get_active(side)
            if pokemon.fainted:
                continue
            ability = ctx.get_ability(pokemon)
            if ability:
                ability.on_end_turn(ctx, pokemon)

        # ── End-of-turn item hooks (Leftovers, Black Sludge, berries) ─
        for side in ("p1", "p2"):
            pokemon = ctx.get_active(side)
            if pokemon.fainted:
                continue
            item = ctx.get_item(pokemon)
            if item:
                item.on_end_turn(ctx, pokemon)

        # ── Weather / terrain countdown ─────────────────────────────
        self._tick_field_timers(ctx)

    def _apply_weather_effects(self, ctx: TurnContext) -> None:
        """Apply end-of-turn weather damage (Sandstorm, Hail)."""
        weather = ctx.state.field.weather
        if weather not in (Weather.SANDSTORM, Weather.HAIL):
            return

        immune_types = {"rock", "ground", "steel"} if weather == Weather.SANDSTORM else {"ice"}
        weather_name = "the sandstorm" if weather == Weather.SANDSTORM else "the hail"

        for side in ("p1", "p2"):
            player = ctx.get_player(side)
            pokemon = player.team[player.active_index]
            if pokemon.fainted:
                continue
            if any(t in immune_types for t in pokemon.types):
                continue

            dmg = max(1, pokemon.max_hp // 16)
            ctx.apply_damage(pokemon, dmg)
            ctx.log.append(f"{pokemon.name} is buffeted by {weather_name}!")

            if pokemon.fainted:
                ctx.log.append(f"{pokemon.name} fainted!")
                self._handle_faint(ctx, player)

    def _apply_terrain_effects(self, ctx: TurnContext) -> None:
        """Apply end-of-turn terrain effects (Grassy Terrain heals grounded Pokemon)."""
        if ctx.state.field.terrain != Terrain.GRASSY:
            return

        for side in ("p1", "p2"):
            player = ctx.get_player(side)
            pokemon = player.team[player.active_index]
            if pokemon.fainted:
                continue

            heal = max(1, pokemon.max_hp // 16)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name} is healed by Grassy Terrain!")

    def _tick_field_timers(self, ctx: TurnContext) -> None:
        """Decrement weather and terrain turn counters; clear on expiry."""
        field = ctx.state.field

        if field.weather != Weather.NONE and field.weather_turns > 0:
            field.weather_turns -= 1
            if field.weather_turns == 0:
                weather_name = {
                    Weather.SUN: "The sunlight faded.",
                    Weather.RAIN: "The rain stopped.",
                    Weather.SANDSTORM: "The sandstorm subsided.",
                    Weather.HAIL: "The hail stopped.",
                }.get(field.weather, "The weather cleared.")
                ctx.log.append(weather_name)
                field.weather = Weather.NONE

        if field.terrain != Terrain.NONE and field.terrain_turns > 0:
            field.terrain_turns -= 1
            if field.terrain_turns == 0:
                ctx.log.append("The terrain returned to normal.")
                field.terrain = Terrain.NONE

    # ─── Faint handling ────────────────────────────────────────────────

    def _handle_faint(self, ctx: TurnContext, player: PlayerState) -> None:
        """Handle a fainted active mon: auto-switch if 1 option, else flag for player choice."""
        alive = [(i, m) for i, m in enumerate(player.team) if not m.fainted]
        if not alive:
            return  # All fainted — battle end check will handle

        if len(alive) == 1:
            # Only one option: auto-switch with hazards/abilities
            idx = alive[0][0]
            player.active_index = idx
            new_mon = player.team[idx]
            ctx.log.append(f"Go, {new_mon.name}!")
            side = "p1" if player is ctx.state.player1 else "p2"
            apply_switch_in_hazards(ctx, new_mon, side, self._rng)
            if new_mon.fainted:
                ctx.log.append(f"{new_mon.name} fainted!")
                return  # Last mon fainted, battle over
            new_ability = ctx.get_ability(new_mon)
            if new_ability:
                new_ability.on_switch_in(ctx, new_mon, side)
        else:
            # Multiple options: player must choose
            ctx.pending_forced_switches.append(player.user_id)

    def apply_forced_switch(
        self, state: BattleState, user_id: str, switch_to: int
    ) -> ForcedSwitchResult:
        """Apply a player's forced switch choice after a faint."""
        ctx = TurnContext(copy.deepcopy(state), self._rng)
        side = ctx.side_for_user(user_id)
        player = ctx.get_player(side)

        player.active_index = switch_to
        new_mon = player.team[switch_to]
        ctx.log.append(f"Go, {new_mon.name}!")

        # Apply entry hazards
        apply_switch_in_hazards(ctx, new_mon, side, self._rng)

        needs_switch = False
        if new_mon.fainted:
            ctx.log.append(f"{new_mon.name} fainted!")
            alive = [(i, m) for i, m in enumerate(player.team) if not m.fainted]
            if not alive:
                ctx.state.status = BattleStatus.ENDED
                opp = ctx.get_opponent_side(side)
                ctx.state.winner_id = ctx.get_player(opp).user_id
            elif len(alive) == 1:
                # Auto-switch to last mon
                idx = alive[0][0]
                player.active_index = idx
                last_mon = player.team[idx]
                ctx.log.append(f"Go, {last_mon.name}!")
                apply_switch_in_hazards(ctx, last_mon, side, self._rng)
                if last_mon.fainted:
                    ctx.log.append(f"{last_mon.name} fainted!")
                    ctx.state.status = BattleStatus.ENDED
                    opp = ctx.get_opponent_side(side)
                    ctx.state.winner_id = ctx.get_player(opp).user_id
                else:
                    ability = ctx.get_ability(last_mon)
                    if ability:
                        ability.on_switch_in(ctx, last_mon, side)
            else:
                needs_switch = True
        else:
            ability = ctx.get_ability(new_mon)
            if ability:
                ability.on_switch_in(ctx, new_mon, side)

        ctx.state.log.extend(ctx.log)

        return ForcedSwitchResult(
            new_state=ctx.state,
            log_entries=ctx.log,
            needs_switch=needs_switch,
            battle_over=ctx.state.status == BattleStatus.ENDED,
            winner_id=ctx.state.winner_id,
        )

    # ─── Battle end check ────────────────────────────────────────────────

    def _check_battle_end(self, ctx: TurnContext) -> None:
        p1_alive = any(not m.fainted for m in ctx.state.player1.team)
        p2_alive = any(not m.fainted for m in ctx.state.player2.team)

        if p1_alive and p2_alive:
            return

        ctx.state.status = BattleStatus.ENDED
        if p1_alive:
            ctx.state.winner_id = ctx.state.player1.user_id
        elif p2_alive:
            ctx.state.winner_id = ctx.state.player2.user_id


# ─── Legacy wrapper for handlers.py ─────────────────────────────────────────

_default_engine = TurnEngine()


def resolve_turn(state: BattleState, move_p1: int, move_p2: int) -> TurnResult:
    """Legacy wrapper: converts move indices to MoveAction objects and resolves."""
    action_p1 = MoveAction(
        player_id=state.player1.user_id,
        move_index=move_p1,
    )
    action_p2 = MoveAction(
        player_id=state.player2.user_id,
        move_index=move_p2,
    )
    return _default_engine.resolve_turn(state, action_p1, action_p2)
