import random
import unittest

from cursed_doll import format_rolls, roll_dice_for_players


class RollDiceForPlayersTest(unittest.TestCase):
    def test_rolls_six_dice_for_each_player(self):
        rolls = roll_dice_for_players(3, rng=random.Random(7))

        self.assertEqual(3, len(rolls))
        self.assertTrue(all(len(player_rolls) == 6 for player_rolls in rolls))
        self.assertTrue(all(1 <= die <= 6 for player_rolls in rolls for die in player_rolls))

    def test_format_rolls_outputs_each_player(self):
        output = format_rolls([[1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]])

        self.assertEqual(
            "Player 1: 1, 2, 3, 4, 5, 6\nPlayer 2: 6, 5, 4, 3, 2, 1",
            output,
        )

    def test_requires_at_least_one_player(self):
        with self.assertRaises(ValueError):
            roll_dice_for_players(0)


if __name__ == "__main__":
    unittest.main()
