"""Move effect data for common competitive moves.

Each entry maps a move name (lowercase, hyphenated) to a MoveEffectSpec.
Only moves with secondary/additional effects need entries — pure-damage
moves like Tackle or Earthquake work fine without one.

Data sourced from Bulbapedia / Pokemon Showdown (Gen V+ mechanics).
"""

from app.battle.effects.base import MoveEffectSpec, StatChange
from app.battle.effects.registry import register_custom_move, register_move_effect
from app.battle.enums import StatusCondition, Weather


def _r(name: str, spec: MoveEffectSpec) -> None:
    register_move_effect(name, spec)


# ─── Fire moves ──────────────────────────────────────────────────────────────

_r("flamethrower", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10))
_r("fire-blast", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10))
_r("ember", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10))
_r("lava-plume", MoveEffectSpec(status=StatusCondition.BURN, status_chance=30))
_r("scald", MoveEffectSpec(status=StatusCondition.BURN, status_chance=30))
_r("sacred-fire", MoveEffectSpec(status=StatusCondition.BURN, status_chance=50))
_r(
    "flare-blitz",
    MoveEffectSpec(
        status=StatusCondition.BURN,
        status_chance=10,
        recoil_fraction=1 / 3,
    ),
)
_r("fire-punch", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10))
_r("heat-wave", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10))
_r(
    "overheat",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="special_attack", stages=-2)],
    ),
)
_r(
    "v-create",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="defense", stages=-1),
            StatChange(stat="special_defense", stages=-1),
            StatChange(stat="speed", stages=-1),
        ],
    ),
)

# ─── Electric moves ─────────────────────────────────────────────────────────

_r("thunderbolt", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=10))
_r("thunder", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=30))
_r("discharge", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=30))
_r("thunder-punch", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=10))
_r("spark", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=30))
_r("nuzzle", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=100))
_r(
    "volt-tackle",
    MoveEffectSpec(
        status=StatusCondition.PARALYSIS,
        status_chance=10,
        recoil_fraction=1 / 3,
    ),
)
_r("wild-charge", MoveEffectSpec(recoil_fraction=1 / 4))

# ─── Ice moves ───────────────────────────────────────────────────────────────

_r("ice-beam", MoveEffectSpec(status=StatusCondition.FREEZE, status_chance=10))
_r("blizzard", MoveEffectSpec(status=StatusCondition.FREEZE, status_chance=10))
_r("ice-punch", MoveEffectSpec(status=StatusCondition.FREEZE, status_chance=10))

# ─── Poison moves ───────────────────────────────────────────────────────────

_r("sludge-bomb", MoveEffectSpec(status=StatusCondition.POISON, status_chance=30))
_r("sludge-wave", MoveEffectSpec(status=StatusCondition.POISON, status_chance=10))
_r("poison-jab", MoveEffectSpec(status=StatusCondition.POISON, status_chance=30))
_r("gunk-shot", MoveEffectSpec(status=StatusCondition.POISON, status_chance=30))
_r("toxic", MoveEffectSpec(status=StatusCondition.TOXIC, status_chance=100))

# ─── Fighting moves ─────────────────────────────────────────────────────────

_r(
    "close-combat",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="defense", stages=-1),
            StatChange(stat="special_defense", stages=-1),
        ],
    ),
)
_r(
    "superpower",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=-1),
            StatChange(stat="defense", stages=-1),
        ],
    ),
)
_r(
    "hammer-arm",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="speed", stages=-1)],
    ),
)
_r(
    "low-sweep",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-1)],
    ),
)
_r("drain-punch", MoveEffectSpec(drain_fraction=0.5))

# ─── Normal moves ───────────────────────────────────────────────────────────

_r("body-slam", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=30))
_r("double-edge", MoveEffectSpec(recoil_fraction=1 / 3))
_r("take-down", MoveEffectSpec(recoil_fraction=1 / 4))
_r("head-smash", MoveEffectSpec(recoil_fraction=1 / 2))
_r("fake-out", MoveEffectSpec(flinch_chance=100))

# ─── Steel moves ────────────────────────────────────────────────────────────

_r("iron-head", MoveEffectSpec(flinch_chance=30))
_r(
    "iron-tail",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
        stat_chance=30,
    ),
)
_r(
    "flash-cannon",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=10,
    ),
)
_r(
    "meteor-mash",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="attack", stages=1)],
    ),
)

# ─── Dark moves ──────────────────────────────────────────────────────────────

_r("dark-pulse", MoveEffectSpec(flinch_chance=20))
_r(
    "crunch",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
        stat_chance=20,
    ),
)

# ─── Rock moves ─────────────────────────────────────────────────────────────

_r("rock-slide", MoveEffectSpec(flinch_chance=30))
_r("stone-edge", MoveEffectSpec())  # high crit ratio (handled via crit_stage, not here)

# ─── Water moves ─────────────────────────────────────────────────────────────

_r("waterfall", MoveEffectSpec(flinch_chance=20))

# ─── Flying moves ───────────────────────────────────────────────────────────

_r("air-slash", MoveEffectSpec(flinch_chance=30))
_r("brave-bird", MoveEffectSpec(recoil_fraction=1 / 3))

# ─── Psychic moves ──────────────────────────────────────────────────────────

_r(
    "psychic",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=10,
    ),
)
_r("zen-headbutt", MoveEffectSpec(flinch_chance=20))

# ─── Ghost moves ────────────────────────────────────────────────────────────

_r(
    "shadow-ball",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=20,
    ),
)

# ─── Dragon moves ───────────────────────────────────────────────────────────

_r("outrage", MoveEffectSpec())  # confusion after 2-3 turns (unique, handled later)
_r(
    "draco-meteor",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="special_attack", stages=-2)],
    ),
)
_r("dragon-claw", MoveEffectSpec())

# ─── Bug moves ───────────────────────────────────────────────────────────────

_r(
    "bug-buzz",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=10,
    ),
)
_r("u-turn", MoveEffectSpec())  # switch-out effect (unique, handled later)

# ─── Ground moves ───────────────────────────────────────────────────────────

_r(
    "earth-power",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=10,
    ),
)
_r(
    "mud-slap",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="accuracy", stages=-1)],
    ),
)

# ─── Grass moves ─────────────────────────────────────────────────────────────

_r(
    "energy-ball",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=10,
    ),
)
_r(
    "leaf-storm",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="special_attack", stages=-2)],
    ),
)
_r("giga-drain", MoveEffectSpec(drain_fraction=0.5))
_r(
    "seed-flare",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-2)],
        stat_chance=40,
    ),
)

# ─── Fairy moves ─────────────────────────────────────────────────────────────

_r(
    "moonblast",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_attack", stages=-1)],
        stat_chance=30,
    ),
)
_r(
    "play-rough",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="attack", stages=-1)],
        stat_chance=10,
    ),
)

# ─── Status moves (pure stat changers) ──────────────────────────────────────

_r(
    "swords-dance",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="attack", stages=2)],
    ),
)
_r(
    "nasty-plot",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="special_attack", stages=2)],
    ),
)
_r(
    "dragon-dance",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="speed", stages=1),
        ],
    ),
)
_r(
    "calm-mind",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="special_attack", stages=1),
            StatChange(stat="special_defense", stages=1),
        ],
    ),
)
_r(
    "bulk-up",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="defense", stages=1),
        ],
    ),
)
_r(
    "quiver-dance",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="special_attack", stages=1),
            StatChange(stat="special_defense", stages=1),
            StatChange(stat="speed", stages=1),
        ],
    ),
)
_r(
    "shell-smash",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=2),
            StatChange(stat="special_attack", stages=2),
            StatChange(stat="speed", stages=2),
            StatChange(stat="defense", stages=-1),
            StatChange(stat="special_defense", stages=-1),
        ],
    ),
)
_r(
    "iron-defense",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="defense", stages=2)],
    ),
)
_r(
    "agility",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="speed", stages=2)],
    ),
)
_r(
    "amnesia",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="special_defense", stages=2)],
    ),
)
_r(
    "growl",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="attack", stages=-1)],
    ),
)
_r(
    "leer",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
    ),
)
_r(
    "screech",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-2)],
    ),
)
_r(
    "charm",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="attack", stages=-2)],
    ),
)
_r(
    "fake-tears",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-2)],
    ),
)
_r(
    "tail-whip",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
    ),
)
_r(
    "string-shot",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-2)],
    ),
)
_r(
    "cotton-spore",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-2)],
    ),
)
_r("will-o-wisp", MoveEffectSpec(status=StatusCondition.BURN, status_chance=100))
_r("thunder-wave", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=100))
_r("spore", MoveEffectSpec(status=StatusCondition.SLEEP, status_chance=100))
_r("sleep-powder", MoveEffectSpec(status=StatusCondition.SLEEP, status_chance=100))
_r("hypnosis", MoveEffectSpec(status=StatusCondition.SLEEP, status_chance=100))
_r("stun-spore", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=100))
_r("poison-powder", MoveEffectSpec(status=StatusCondition.POISON, status_chance=100))

# ─── Weather moves ──────────────────────────────────────────────────────────

_r("sunny-day", MoveEffectSpec(weather=Weather.SUN))
_r("rain-dance", MoveEffectSpec(weather=Weather.RAIN))
_r("sandstorm", MoveEffectSpec(weather=Weather.SANDSTORM))
_r("hail", MoveEffectSpec(weather=Weather.HAIL))

# ─── Hazard moves (custom handlers) ────────────────────────────────────────

from app.battle.effects.moves.hazards import (  # noqa: E402
    clear_all_hazards,
    clear_own_hazards,
    set_spikes,
    set_stealth_rock,
    set_toxic_spikes,
)
from app.battle.effects.moves.protect import try_protect  # noqa: E402


def _stealth_rock_handler(ctx, attacker, defender, rng):
    opp_side = ctx.get_opponent_side(ctx.side_for_user(attacker.name))
    # We need the side, not the user — find it from attacker identity
    for side in ("p1", "p2"):
        if ctx.get_active(side) is attacker:
            opp_side = ctx.get_opponent_side(side)
            break
    set_stealth_rock(ctx, attacker, opp_side)


def _spikes_handler(ctx, attacker, defender, rng):
    for side in ("p1", "p2"):
        if ctx.get_active(side) is attacker:
            opp_side = ctx.get_opponent_side(side)
            break
    set_spikes(ctx, attacker, opp_side)


def _toxic_spikes_handler(ctx, attacker, defender, rng):
    for side in ("p1", "p2"):
        if ctx.get_active(side) is attacker:
            opp_side = ctx.get_opponent_side(side)
            break
    set_toxic_spikes(ctx, attacker, opp_side)


def _defog_handler(ctx, attacker, defender, rng):
    for side in ("p1", "p2"):
        if ctx.get_active(side) is attacker:
            clear_all_hazards(ctx, side)
            break


def _protect_handler(ctx, attacker, defender, rng):
    try_protect(ctx, attacker, rng)


register_custom_move("stealth-rock", _stealth_rock_handler)
register_custom_move("spikes", _spikes_handler)
register_custom_move("toxic-spikes", _toxic_spikes_handler)
register_custom_move("defog", _defog_handler)
register_custom_move("protect", _protect_handler)
register_custom_move("detect", _protect_handler)


def _rapid_spin_handler(ctx, attacker, defender, rng):
    """Rapid Spin: clears hazards on user's side after dealing damage."""
    for side in ("p1", "p2"):
        if ctx.get_active(side) is attacker:
            clear_own_hazards(ctx, side)
            break


register_custom_move("rapid-spin", _rapid_spin_handler)


# ─── Additional Fire moves ─────────────────────────────────────────────────

_r("fire-fang", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10, flinch_chance=10))
_r("inferno", MoveEffectSpec(status=StatusCondition.BURN, status_chance=100))
_r("blue-flare", MoveEffectSpec(status=StatusCondition.BURN, status_chance=20))
_r("magma-storm", MoveEffectSpec(status=StatusCondition.BURN, status_chance=0))  # trapping
_r(
    "mystical-fire",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_attack", stages=-1)],
    ),
)
_r("pyro-ball", MoveEffectSpec(status=StatusCondition.BURN, status_chance=10))

# ─── Additional Electric moves ─────────────────────────────────────────────

_r(
    "thunder-fang",
    MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=10, flinch_chance=10),
)
_r("bolt-strike", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=20))
_r(
    "thunderous-kick",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
    ),
)

# ─── Additional Ice moves ──────────────────────────────────────────────────

_r("ice-fang", MoveEffectSpec(status=StatusCondition.FREEZE, status_chance=10, flinch_chance=10))
_r("freeze-dry", MoveEffectSpec(status=StatusCondition.FREEZE, status_chance=10))
_r(
    "icy-wind",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-1)],
    ),
)
_r(
    "glaciate",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-1)],
    ),
)

# ─── Additional Water moves ────────────────────────────────────────────────

_r(
    "muddy-water",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="accuracy", stages=-1)],
        stat_chance=30,
    ),
)
_r(
    "liquidation",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
        stat_chance=20,
    ),
)
_r("steam-eruption", MoveEffectSpec(status=StatusCondition.BURN, status_chance=30))
_r("origin-pulse", MoveEffectSpec())
_r("aqua-jet", MoveEffectSpec())  # +1 priority handled by move data

# ─── Additional Fighting moves ─────────────────────────────────────────────

_r("aura-sphere", MoveEffectSpec())  # never misses
_r(
    "focus-blast",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=10,
    ),
)
_r("mach-punch", MoveEffectSpec())  # +1 priority
_r(
    "power-up-punch",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="attack", stages=1)],
    ),
)
_r("sacred-sword", MoveEffectSpec())  # ignores stat changes

# ─── Additional Normal moves ───────────────────────────────────────────────

_r("extreme-speed", MoveEffectSpec())  # +2 priority
_r("quick-attack", MoveEffectSpec())  # +1 priority
_r("sucker-punch", MoveEffectSpec())  # +1 priority conditional
_r("tri-attack", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=20))
_r("return", MoveEffectSpec())
_r("hyper-voice", MoveEffectSpec())
_r("boomburst", MoveEffectSpec())
_r(
    "crush-claw",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="defense", stages=-1)],
        stat_chance=50,
    ),
)

# ─── Additional Dark moves ─────────────────────────────────────────────────

_r("knock-off", MoveEffectSpec())
_r("sucker-punch", MoveEffectSpec())
_r("pursuit", MoveEffectSpec())
_r("throat-chop", MoveEffectSpec())
_r("foul-play", MoveEffectSpec())

# ─── Additional Poison moves ───────────────────────────────────────────────

_r("cross-poison", MoveEffectSpec(status=StatusCondition.POISON, status_chance=10))
_r("poison-fang", MoveEffectSpec(status=StatusCondition.TOXIC, status_chance=50))
_r("venoshock", MoveEffectSpec())  # doubles power if target poisoned

# ─── Additional Psychic moves ──────────────────────────────────────────────

_r("psyshock", MoveEffectSpec())  # special move that uses physical defense
_r("future-sight", MoveEffectSpec())
_r("expanding-force", MoveEffectSpec())
_r(
    "luster-purge",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_defense", stages=-1)],
        stat_chance=50,
    ),
)

# ─── Additional Ghost moves ────────────────────────────────────────────────

_r("phantom-force", MoveEffectSpec())
_r("poltergeist", MoveEffectSpec())
_r("spectral-thief", MoveEffectSpec())
_r("spirit-shackle", MoveEffectSpec())

# ─── Additional Dragon moves ───────────────────────────────────────────────

_r("dragon-pulse", MoveEffectSpec())
_r("dragon-rush", MoveEffectSpec(flinch_chance=20))
_r(
    "scale-shot",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="speed", stages=1),
            StatChange(stat="defense", stages=-1),
        ],
    ),
)

# ─── Additional Fairy moves ────────────────────────────────────────────────

_r("dazzling-gleam", MoveEffectSpec())
_r("draining-kiss", MoveEffectSpec(drain_fraction=0.75))
_r(
    "spirit-break",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_attack", stages=-1)],
    ),
)

# ─── Additional Flying moves ───────────────────────────────────────────────

_r("hurricane", MoveEffectSpec(status=StatusCondition.PARALYSIS, status_chance=0))  # confusion 30%
_r("acrobatics", MoveEffectSpec())
_r("drill-peck", MoveEffectSpec())

# ─── Additional Ground moves ───────────────────────────────────────────────

_r("earthquake", MoveEffectSpec())
_r("high-horsepower", MoveEffectSpec())
_r("scorching-sands", MoveEffectSpec(status=StatusCondition.BURN, status_chance=30))
_r("stomping-tantrum", MoveEffectSpec())

# ─── Additional Rock moves ─────────────────────────────────────────────────

_r("power-gem", MoveEffectSpec())
_r("head-smash", MoveEffectSpec(recoil_fraction=0.5))
_r(
    "diamond-storm",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="defense", stages=2)],
    ),
)
_r("accelerock", MoveEffectSpec())  # +1 priority

# ─── Additional Steel moves ────────────────────────────────────────────────

_r("bullet-punch", MoveEffectSpec())  # +1 priority
_r("heavy-slam", MoveEffectSpec())
_r("gyro-ball", MoveEffectSpec())  # power based on speed diff
_r("king-shield", MoveEffectSpec())

# ─── Additional Grass moves ────────────────────────────────────────────────

_r("power-whip", MoveEffectSpec())
_r("horn-leech", MoveEffectSpec(drain_fraction=0.5))
_r("wood-hammer", MoveEffectSpec(recoil_fraction=1 / 3))
_r("grassy-glide", MoveEffectSpec())  # priority in grassy terrain

# ─── Additional Bug moves ──────────────────────────────────────────────────

_r("leech-life", MoveEffectSpec(drain_fraction=0.5))
_r("first-impression", MoveEffectSpec())  # +2 priority, only works turn 1
_r(
    "lunge",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="attack", stages=-1)],
    ),
)
_r("x-scissor", MoveEffectSpec())

# ─── Additional status moves ───────────────────────────────────────────────

_r("roost", MoveEffectSpec())  # recovery handled specially
_r("recover", MoveEffectSpec())
_r("wish", MoveEffectSpec())
_r("stealth-rock", MoveEffectSpec())  # custom handler
_r("defog", MoveEffectSpec())  # custom handler
_r("taunt", MoveEffectSpec())
_r("encore", MoveEffectSpec())
_r("trick-room", MoveEffectSpec())
_r("tailwind", MoveEffectSpec())
_r("light-screen", MoveEffectSpec())
_r("reflect", MoveEffectSpec())
_r("substitute", MoveEffectSpec())
_r("leech-seed", MoveEffectSpec())
_r("whirlwind", MoveEffectSpec())  # phazing
_r("roar", MoveEffectSpec())  # phazing
_r("toxic-spikes", MoveEffectSpec())  # custom handler
_r("sticky-web", MoveEffectSpec())  # custom handler
_r("rest", MoveEffectSpec(status=StatusCondition.SLEEP, status_chance=100))

# ─── Setup moves ────────────────────────────────────────────────────────────

_r(
    "coil",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="defense", stages=1),
            StatChange(stat="accuracy", stages=1),
        ],
    ),
)
_r(
    "rock-polish",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="speed", stages=2)],
    ),
)
_r(
    "hone-claws",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="accuracy", stages=1),
        ],
    ),
)
_r(
    "shift-gear",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="speed", stages=2),
        ],
    ),
)
_r(
    "work-up",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="special_attack", stages=1),
        ],
    ),
)
_r(
    "growth",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="special_attack", stages=1),
        ],
    ),
)
_r(
    "curse",
    MoveEffectSpec(
        self_stat_changes=[
            StatChange(stat="attack", stages=1),
            StatChange(stat="defense", stages=1),
            StatChange(stat="speed", stages=-1),
        ],
    ),
)
_r(
    "belly-drum",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="attack", stages=6)],
    ),
)
_r(
    "swords-dance",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="attack", stages=2)],
    ),
)
_r(
    "tail-glow",
    MoveEffectSpec(
        self_stat_changes=[StatChange(stat="special_attack", stages=3)],
    ),
)

# ─── Debuff moves ──────────────────────────────────────────────────────────

_r(
    "icy-wind",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-1)],
    ),
)
_r(
    "electroweb",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="speed", stages=-1)],
    ),
)
_r(
    "eerie-impulse",
    MoveEffectSpec(
        stat_changes=[StatChange(stat="special_attack", stages=-2)],
    ),
)
_r(
    "tickle",
    MoveEffectSpec(
        stat_changes=[
            StatChange(stat="attack", stages=-1),
            StatChange(stat="defense", stages=-1),
        ],
    ),
)
_r(
    "memento",
    MoveEffectSpec(
        stat_changes=[
            StatChange(stat="attack", stages=-2),
            StatChange(stat="special_attack", stages=-2),
        ],
    ),
)
_r(
    "parting-shot",
    MoveEffectSpec(
        stat_changes=[
            StatChange(stat="attack", stages=-1),
            StatChange(stat="special_attack", stages=-1),
        ],
    ),
)
