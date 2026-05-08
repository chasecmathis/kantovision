"""Miscellaneous ability implementations — batch 2.

Covers: Clear Body, Thick Fat, Serene Grace, Moxie, Sheer Force,
Iron Fist, Tinted Lens, Prankster, Contrary, Unaware, Defiant,
Competitive, Magic Guard, Poison Heal, Overcoat, Quick Feet,
Toxic Boost, Flare Boost, No Guard, Rain Dish, Ice Body,
Dry Skin, Solar Power, Skill Link.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.battle.effects.base import AbilityEffect
from app.battle.effects.registry import register_ability
from app.battle.enums import StatusCondition, Weather

if TYPE_CHECKING:
    from app.battle.pipeline import TurnContext
    from app.battle.state import MoveSlot, PokemonBattleState


# ─── Stat-protection abilities ──────────────────────────────────────────────


@register_ability
class ClearBody(AbilityEffect):
    """Prevents stat drops from opponents."""

    name = "clear-body"

    def on_stat_change(
        self, ctx: TurnContext, pokemon: PokemonBattleState, stat: str, stages: int
    ) -> int:
        if stages < 0:
            ctx.log.append(f"{pokemon.name}'s Clear Body prevents stat loss!")
            return 0
        return stages


@register_ability
class WhiteSmoke(AbilityEffect):
    """Same as Clear Body."""

    name = "white-smoke"

    def on_stat_change(
        self, ctx: TurnContext, pokemon: PokemonBattleState, stat: str, stages: int
    ) -> int:
        if stages < 0:
            ctx.log.append(f"{pokemon.name}'s White Smoke prevents stat loss!")
            return 0
        return stages


@register_ability
class Contrary(AbilityEffect):
    """Stat changes are reversed."""

    name = "contrary"

    def on_stat_change(
        self, ctx: TurnContext, pokemon: PokemonBattleState, stat: str, stages: int
    ) -> int:
        return -stages


@register_ability
class Defiant(AbilityEffect):
    """Attack rises by 2 stages when any stat is lowered."""

    name = "defiant"

    def on_stat_change(
        self, ctx: TurnContext, pokemon: PokemonBattleState, stat: str, stages: int
    ) -> int:
        if stages < 0:
            ctx.apply_stat_change(pokemon, "attack", 2, source=f"{pokemon.name}'s Defiant")
        return stages


@register_ability
class Competitive(AbilityEffect):
    """Special Attack rises by 2 stages when any stat is lowered."""

    name = "competitive"

    def on_stat_change(
        self, ctx: TurnContext, pokemon: PokemonBattleState, stat: str, stages: int
    ) -> int:
        if stages < 0:
            ctx.apply_stat_change(
                pokemon, "special_attack", 2, source=f"{pokemon.name}'s Competitive"
            )
        return stages


# ─── Damage modifiers ──────────────────────────────────────────────────────


@register_ability
class ThickFat(AbilityEffect):
    """Halves damage from Fire and Ice moves."""

    name = "thick-fat"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.type in ("fire", "ice") and defender.ability == "thick-fat":
            return damage // 2
        return damage


@register_ability
class TintedLens(AbilityEffect):
    """Not very effective moves deal double damage."""

    name = "tinted-lens"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        from app.battle.typechart import get_type_effectiveness

        eff = get_type_effectiveness(move.type, defender.types)
        if 0 < eff < 1:
            return damage * 2
        return damage


@register_ability
class SheerForce(AbilityEffect):
    """1.3x damage for moves with secondary effects; secondary effects are removed."""

    name = "sheer-force"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        from app.battle.effects.registry import MOVE_EFFECT_REGISTRY

        spec = MOVE_EFFECT_REGISTRY.get(move.name)
        if spec and (spec.status_chance or spec.flinch_chance or spec.stat_changes):
            return int(damage * 1.3)
        return damage


@register_ability
class IronFist(AbilityEffect):
    """1.2x damage for punch moves."""

    name = "iron-fist"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if "punch" in move.flags:
            return int(damage * 1.2)
        return damage


@register_ability
class StrongJaw(AbilityEffect):
    """1.5x damage for bite moves."""

    name = "strong-jaw"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if "bite" in move.flags:
            return int(damage * 1.5)
        return damage


@register_ability
class ToxicBoost(AbilityEffect):
    """1.5x physical damage when poisoned."""

    name = "toxic-boost"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.category == "physical" and attacker.status in (
            StatusCondition.POISON,
            StatusCondition.TOXIC,
        ):
            return int(damage * 1.5)
        return damage


@register_ability
class FlareBoost(AbilityEffect):
    """1.5x special damage when burned."""

    name = "flare-boost"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.category == "special" and attacker.status == StatusCondition.BURN:
            return int(damage * 1.5)
        return damage


# ─── Speed modifiers ──────────────────────────────────────────────────────


@register_ability
class QuickFeet(AbilityEffect):
    """1.5x speed when statused."""

    name = "quick-feet"

    def on_modify_speed(self, ctx: TurnContext, pokemon: PokemonBattleState, speed: int) -> int:
        if pokemon.status != StatusCondition.NONE:
            return int(speed * 1.5)
        return speed


# ─── End-of-turn abilities ──────────────────────────────────────────────────


@register_ability
class PoisonHeal(AbilityEffect):
    """Heals 1/8 max HP per turn when poisoned (instead of taking damage)."""

    name = "poison-heal"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if pokemon.status in (StatusCondition.POISON, StatusCondition.TOXIC):
            heal = max(1, pokemon.max_hp // 8)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name}'s Poison Heal restored HP!")


@register_ability
class RainDish(AbilityEffect):
    """Heals 1/16 max HP per turn in rain."""

    name = "rain-dish"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if ctx.state.field.weather == Weather.RAIN:
            heal = max(1, pokemon.max_hp // 16)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name}'s Rain Dish restored HP!")


@register_ability
class IceBody(AbilityEffect):
    """Heals 1/16 max HP per turn in hail."""

    name = "ice-body"

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if ctx.state.field.weather == Weather.HAIL:
            heal = max(1, pokemon.max_hp // 16)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name}'s Ice Body restored HP!")


@register_ability
class SolarPower(AbilityEffect):
    """In sun: 1.5x SpA but loses 1/8 HP per turn."""

    name = "solar-power"

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if ctx.state.field.weather == Weather.SUN and move.category == "special":
            return int(damage * 1.5)
        return damage

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if ctx.state.field.weather == Weather.SUN:
            dmg = max(1, pokemon.max_hp // 8)
            ctx.apply_damage(pokemon, dmg)
            ctx.log.append(f"{pokemon.name} was hurt by its Solar Power!")


@register_ability
class DrySkin(AbilityEffect):
    """Heals 1/8 in rain, takes 1/8 damage in sun. Immune to Water, takes 1.25x Fire."""

    name = "dry-skin"

    def on_try_hit(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
    ) -> bool:
        if move.type == "water":
            heal = max(1, defender.max_hp // 4)
            ctx.heal(defender, heal)
            ctx.log.append(f"{defender.name}'s Dry Skin absorbed the Water move!")
            return False
        return True

    def on_modify_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> int:
        if move.type == "fire" and defender.ability == "dry-skin":
            return int(damage * 1.25)
        return damage

    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        if ctx.state.field.weather == Weather.RAIN:
            heal = max(1, pokemon.max_hp // 8)
            healed = ctx.heal(pokemon, heal)
            if healed > 0:
                ctx.log.append(f"{pokemon.name}'s Dry Skin restored HP in the rain!")
        elif ctx.state.field.weather == Weather.SUN:
            dmg = max(1, pokemon.max_hp // 8)
            ctx.apply_damage(pokemon, dmg)
            ctx.log.append(f"{pokemon.name}'s Dry Skin is hurt by the sunlight!")


@register_ability
class MagicGuard(AbilityEffect):
    """Only takes damage from direct attacks (not status, weather, hazards, recoil)."""

    name = "magic-guard"

    # Note: Magic Guard is partially handled — prevents end-of-turn status damage.
    # Full implementation would require engine-level checks for weather/hazard/recoil immunity.
    def on_end_turn(self, ctx: TurnContext, pokemon: PokemonBattleState) -> None:
        # Undo any status damage that was applied this turn by healing it back
        pass  # Handled by the engine checking for magic-guard before applying damage


@register_ability
class Overcoat(AbilityEffect):
    """Immune to weather damage and powder moves."""

    name = "overcoat"


@register_ability
class Moxie(AbilityEffect):
    """Attack rises by 1 stage when the user KOs an opponent."""

    name = "moxie"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if defender.fainted:
            ctx.apply_stat_change(attacker, "attack", 1, source=f"{attacker.name}'s Moxie")


@register_ability
class BeastBoost(AbilityEffect):
    """Boosts highest stat by 1 stage when the user KOs an opponent."""

    name = "beast-boost"

    def on_after_damage(
        self,
        ctx: TurnContext,
        attacker: PokemonBattleState,
        defender: PokemonBattleState,
        move: MoveSlot,
        damage: int,
    ) -> None:
        if defender.fainted:
            stats = {
                "attack": attacker.attack,
                "defense": attacker.defense,
                "special_attack": attacker.special_attack,
                "special_defense": attacker.special_defense,
                "speed": attacker.speed,
            }
            best = max(stats, key=lambda s: stats[s])
            ctx.apply_stat_change(attacker, best, 1, source=f"{attacker.name}'s Beast Boost")


@register_ability
class NoGuard(AbilityEffect):
    """All moves used by or against this Pokemon always hit."""

    name = "no-guard"


@register_ability
class SereneGrace(AbilityEffect):
    """Doubles the chance of secondary effects."""

    name = "serene-grace"


@register_ability
class SkillLink(AbilityEffect):
    """Multi-hit moves always hit the maximum number of times."""

    name = "skill-link"


@register_ability
class Prankster(AbilityEffect):
    """Status moves get +1 priority."""

    name = "prankster"


@register_ability
class SandVeil(AbilityEffect):
    """Evasion increased by 20% in sandstorm."""

    name = "sand-veil"


@register_ability
class SnowCloak(AbilityEffect):
    """Evasion increased by 20% in hail."""

    name = "snow-cloak"


@register_ability
class Unaware(AbilityEffect):
    """Ignores opponent's stat changes when taking or dealing damage."""

    name = "unaware"


@register_ability
class Scrappy(AbilityEffect):
    """Normal and Fighting moves can hit Ghost types."""

    name = "scrappy"
