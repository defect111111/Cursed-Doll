import unittest

from cursed_doll import (
    FACE_VALUES,
    choose_face_interactively,
    choose_face_to_keep,
    choose_stop_interactively,
    format_rolls,
    roll_dice_for_players,
)


class FixedRng:
    def __init__(self, values):
        self.values = list(values)

    def randint(self, minimum, maximum):
        value = self.values.pop(0)
        if not minimum <= value <= maximum:
            raise AssertionError(f"{value} is outside {minimum}-{maximum}")
        return value


class RollDiceForPlayersTest(unittest.TestCase):
    def test_keeps_matching_faces_until_total_reaches_at_least_seven(self):
        rng = FixedRng([1, 1, 2, 3, 4, 6, 3, 3, 5, 6])

        results = roll_dice_for_players(1, rng=rng)

        self.assertEqual(
            [
                {
                    "roll": ["1", "1", "2", "3", "4", "two dolls"],
                    "kept_face": "1",
                    "kept_dice": ["1", "1"],
                    "kept_total": 2,
                    "remaining_dice": 4,
                    "can_stop": False,
                    "stopped": False,
                },
                {
                    "roll": ["3", "3", "one doll", "two dolls"],
                    "kept_face": "3",
                    "kept_dice": ["3", "3"],
                    "kept_total": 8,
                    "remaining_dice": 2,
                    "can_stop": True,
                    "stopped": True,
                },
            ],
            results[0]["turns"],
        )
        self.assertEqual(["1", "1", "3", "3"], results[0]["kept_dice"])
        self.assertEqual(8, results[0]["kept_total"])
        self.assertEqual(2, results[0]["ignored_dice"])
        self.assertTrue(results[0]["stopped"])

    def test_doll_faces_do_not_add_to_the_kept_total(self):
        self.assertEqual(0, FACE_VALUES["one doll"])
        self.assertEqual(0, FACE_VALUES["two dolls"])

    def test_player_can_stop_when_kept_total_is_larger_than_seven(self):
        rng = FixedRng([4, 4, 4, 1, 2, 3])

        results = roll_dice_for_players(1, rng=rng)

        self.assertEqual(12, results[0]["kept_total"])
        self.assertEqual(3, results[0]["ignored_dice"])
        self.assertTrue(results[0]["turns"][0]["can_stop"])
        self.assertTrue(results[0]["stopped"])

    def test_rolls_for_each_player(self):
        rng = FixedRng([
            1, 1, 1, 1, 1, 1,
            2, 2, 2, 1, 1, 1,
            3, 3, 3,
        ])

        results = roll_dice_for_players(2, rng=rng)

        self.assertEqual(2, len(results))
        self.assertEqual(6, len(results[0]["kept_dice"]))
        self.assertEqual(6, len(results[1]["kept_dice"]))

    def test_format_rolls_outputs_each_player(self):
        output = format_rolls(
            [
                {
                    "turns": [
                        {
                            "roll": ["1", "1", "2", "3", "4", "two dolls"],
                            "kept_face": "1",
                            "kept_dice": ["1", "1"],
                            "kept_total": 2,
                            "remaining_dice": 4,
                            "stopped": False,
                        },
                        {
                            "roll": ["2", "2", "4"],
                            "kept_face": "2",
                            "kept_dice": ["2", "2"],
                            "kept_total": 6,
                            "remaining_dice": 1,
                            "stopped": False,
                        },
                        {
                            "roll": ["one doll"],
                            "kept_face": "one doll",
                            "kept_dice": ["one doll"],
                            "kept_total": 6,
                            "remaining_dice": 0,
                            "stopped": False,
                        },
                    ],
                    "kept_dice": ["1", "1", "2", "2", "one doll"],
                    "kept_total": 6,
                    "ignored_dice": 0,
                    "stopped": False,
                }
            ]
        )

        self.assertEqual(
            "Player 1:\n"
            "  Roll 1: rolled [1, 1, 2, 3, 4, two dolls], kept [1, 1], total 2, 4 dice remaining\n"
            "  Roll 2: rolled [2, 2, 4], kept [2, 2], total 6, 1 die remaining\n"
            "  Roll 3: rolled [one doll], kept [one doll], total 6, 0 dice remaining\n"
            "  Final kept dice: 1, 1, 2, 2, one doll\n"
            "  Final kept total: 6",
            output,
        )

    def test_choose_face_prefers_hitting_seven(self):
        self.assertEqual("4", choose_face_to_keep(["1", "1", "4"], kept_total=3))

    def test_choose_face_can_go_over_seven_to_stop(self):
        self.assertEqual("4", choose_face_to_keep(["4", "4", "one doll"], kept_total=5))

    def test_choose_face_interactively_accepts_lettered_choice(self):
        prompts = []
        output = []

        def fake_input(prompt):
            prompts.append(prompt)
            return "b"

        result = choose_face_interactively(
            ["1", "1", "3", "one doll"],
            kept_total=2,
            player_index=2,
            kept_dice=["3"],
            input_fn=fake_input,
            output_fn=output.append,
        )

        self.assertEqual("1", result)
        self.assertEqual(["> "], prompts)
        self.assertIn("Player 2", output)
        self.assertIn("Kept so far: [3]", output)
        self.assertIn("Rolled: 1, 1, 3, one doll", output)
        self.assertIn("  b. 1 x2 (adds 2, total would be 4)", output)

    def test_choose_stop_interactively_accepts_yes(self):
        prompts = []
        output = []

        def fake_input(prompt):
            prompts.append(prompt)
            return "y"

        self.assertTrue(
            choose_stop_interactively(
                8,
                2,
                player_index=1,
                kept_dice=["4", "4"],
                input_fn=fake_input,
                output_fn=output.append,
            )
        )
        self.assertEqual(["> "], prompts)
        self.assertIn("Player 1", output)
        self.assertIn("Kept so far: [4, 4]", output)
        self.assertIn("Kept total is 8. Stop and ignore 2 dice? [y/n]", output)

    def test_two_players_can_use_interactive_choices(self):
        rng = FixedRng([
            3, 3, 1, 2, 5, 6,
            4, 4, 5, 6,
            1, 2, 3, 4, 5, 6,
            4, 4, 4, 4, 4,
        ])
        choices = iter(["e", "c", "y", "f", "a"])

        def fake_input(prompt):
            return next(choices)

        def choose_face(roll, kept_total=0, **context):
            return choose_face_interactively(
                roll,
                kept_total=kept_total,
                **context,
                input_fn=fake_input,
                output_fn=lambda message: None,
            )

        def should_stop(kept_total, remaining_dice, **context):
            return choose_stop_interactively(
                kept_total,
                remaining_dice,
                **context,
                input_fn=fake_input,
                output_fn=lambda message: None,
            )

        results = roll_dice_for_players(
            2,
            rng=rng,
            choose_face=choose_face,
            should_stop=should_stop,
        )

        self.assertEqual(2, len(results))
        self.assertEqual(["3", "3", "4", "4"], results[0]["kept_dice"])
        self.assertEqual(14, results[0]["kept_total"])
        self.assertEqual(2, results[0]["ignored_dice"])
        self.assertEqual(["4", "4", "4", "4", "4", "4"], results[1]["kept_dice"])
        self.assertEqual(24, results[1]["kept_total"])
        self.assertEqual(0, results[1]["ignored_dice"])

    def test_requires_at_least_one_player(self):
        with self.assertRaises(ValueError):
            roll_dice_for_players(0)


if __name__ == "__main__":
    unittest.main()
