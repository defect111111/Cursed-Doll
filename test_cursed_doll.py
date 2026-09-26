import unittest

from cursed_doll import choose_number_to_keep, format_rolls, roll_dice_for_players


class FixedRng:
    def __init__(self, values):
        self.values = list(values)

    def randint(self, minimum, maximum):
        value = self.values.pop(0)
        if not minimum <= value <= maximum:
            raise AssertionError(f"{value} is outside {minimum}-{maximum}")
        return value


class RollDiceForPlayersTest(unittest.TestCase):
    def test_keeps_matching_dice_and_rerolls_the_rest_until_all_are_kept(self):
        rng = FixedRng([2, 2, 5, 1, 4, 6, 3, 3, 4, 1, 6, 6])

        results = roll_dice_for_players(1, rng=rng)

        self.assertEqual(
            [
                {
                    "roll": [2, 2, 5, 1, 4, 6],
                    "kept_number": 2,
                    "kept_dice": [2, 2],
                    "remaining_dice": 4,
                },
                {
                    "roll": [3, 3, 4, 1],
                    "kept_number": 3,
                    "kept_dice": [3, 3],
                    "remaining_dice": 2,
                },
                {
                    "roll": [6, 6],
                    "kept_number": 6,
                    "kept_dice": [6, 6],
                    "remaining_dice": 0,
                },
            ],
            results[0]["turns"],
        )
        self.assertEqual([2, 2, 3, 3, 6, 6], results[0]["kept_dice"])

    def test_rolls_until_each_player_has_six_kept_dice(self):
        rng = FixedRng([
            1, 1, 1, 1, 1, 1,
            2, 2, 3, 3, 4, 4,
            5, 5, 6, 6,
            1, 1,
        ])

        results = roll_dice_for_players(2, rng=rng)

        self.assertEqual(2, len(results))
        self.assertTrue(all(len(result["kept_dice"]) == 6 for result in results))

    def test_format_rolls_outputs_each_player(self):
        output = format_rolls(
            [
                {
                    "turns": [
                        {
                            "roll": [1, 1, 2, 3, 4, 5],
                            "kept_number": 1,
                            "kept_dice": [1, 1],
                            "remaining_dice": 4,
                        },
                        {
                            "roll": [6, 6, 6, 2],
                            "kept_number": 6,
                            "kept_dice": [6, 6, 6],
                            "remaining_dice": 1,
                        },
                        {
                            "roll": [3],
                            "kept_number": 3,
                            "kept_dice": [3],
                            "remaining_dice": 0,
                        },
                    ],
                    "kept_dice": [1, 1, 6, 6, 6, 3],
                }
            ]
        )

        self.assertEqual(
            "Player 1:\n"
            "  Roll 1: rolled [1, 1, 2, 3, 4, 5], kept [1, 1], 4 dice remaining\n"
            "  Roll 2: rolled [6, 6, 6, 2], kept [6, 6, 6], 1 die remaining\n"
            "  Roll 3: rolled [3], kept [3], 0 dice remaining\n"
            "  Final kept dice: 1, 1, 6, 6, 6, 3",
            output,
        )

    def test_keeps_lowest_number_when_counts_are_tied(self):
        self.assertEqual(2, choose_number_to_keep([6, 2, 6, 2, 5, 4]))

    def test_requires_at_least_one_player(self):
        with self.assertRaises(ValueError):
            roll_dice_for_players(0)


if __name__ == "__main__":
    unittest.main()
