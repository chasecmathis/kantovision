"""Tests for accuracy check mechanics."""

from random import Random

from app.battle.accuracy import accuracy_check
from app.battle.state import StatStages
from tests.helpers import make_move, make_pokemon


class TestAccuracyCheck:
    def test_100_accuracy_always_hits(self):
        """A 100% accurate move should almost always hit at neutral stages."""
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(accuracy=100)
        hits = sum(accuracy_check(attacker, defender, move, Random(seed)) for seed in range(200))
        assert hits == 200

    def test_0_accuracy_always_hits(self):
        """Accuracy=0 means the move never misses (e.g. Swift, Aerial Ace)."""
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(accuracy=0)
        # Even with extreme evasion, accuracy=0 should always hit
        defender.stat_stages.evasion = 6
        for seed in range(50):
            assert accuracy_check(attacker, defender, move, Random(seed)) is True

    def test_low_accuracy_can_miss(self):
        """A low-accuracy move should miss sometimes."""
        attacker = make_pokemon()
        defender = make_pokemon()
        move = make_move(accuracy=50)
        results = [accuracy_check(attacker, defender, move, Random(seed)) for seed in range(200)]
        hits = sum(results)
        misses = len(results) - hits
        assert misses > 0, "Expected some misses with 50% accuracy"
        assert hits > 0, "Expected some hits with 50% accuracy"

    def test_accuracy_stages_improve_hit_rate(self):
        """Positive accuracy stages should increase hit rate."""
        defender = make_pokemon()
        move = make_move(accuracy=50)

        base_attacker = make_pokemon()
        boosted_attacker = make_pokemon(stat_stages=StatStages(accuracy=3))

        base_hits = sum(
            accuracy_check(base_attacker, defender, move, Random(seed)) for seed in range(500)
        )
        boosted_hits = sum(
            accuracy_check(boosted_attacker, defender, move, Random(seed)) for seed in range(500)
        )
        assert boosted_hits > base_hits

    def test_evasion_stages_reduce_hit_rate(self):
        """Positive evasion stages on defender should reduce hit rate."""
        attacker = make_pokemon()
        move = make_move(accuracy=80)

        normal_def = make_pokemon()
        evasive_def = make_pokemon(stat_stages=StatStages(evasion=3))

        normal_hits = sum(
            accuracy_check(attacker, normal_def, move, Random(seed)) for seed in range(500)
        )
        evasive_hits = sum(
            accuracy_check(attacker, evasive_def, move, Random(seed)) for seed in range(500)
        )
        assert evasive_hits < normal_hits
