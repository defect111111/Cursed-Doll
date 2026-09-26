import unittest

from dice import FACE_VALUES, count_dolls
from game import (
    INITIAL_PLAYER_DOLLS,
    choose_gift_recipient_interactively,
    choose_room_interactively,
    create_doll_rooms,
    fullest_adjustable_room,
    fullest_adjustable_rooms,
    format_game_result,
    give_dolls_for_ones,
    move_extra_dolls_for_all_players,
    move_extra_dolls_to_room_eleven,
    place_dolls_for_turn,
    play_game,
    play_game_turns_for_players,
    resolve_turn_effects,
    room_for_total,
)
from player_turn import (
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
                    "ended_because_no_pattern": False,
                },
                {
                    "roll": ["3", "3", "one doll", "two dolls"],
                    "kept_face": "3",
                    "kept_dice": ["3", "3"],
                    "kept_total": 8,
                    "remaining_dice": 2,
                    "can_stop": True,
                    "stopped": True,
                    "ended_because_no_pattern": False,
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

    def test_counts_dolls_in_roll(self):
        self.assertEqual(3, count_dolls(["1", "one doll", "two dolls", "4"]))

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
            "========================================================\n"
            "Player 1 result\n"
            "--------------------------------------------------------\n"
            "Roll 1: rolled [1, 1, 2, 3, 4, two dolls] | kept [1, 1] | total 2 | 4 dice remaining\n"
            "Roll 2: rolled [2, 2, 4] | kept [2, 2] | total 6 | 1 die remaining\n"
            "Roll 3: rolled [one doll] | kept [one doll] | total 6 | 0 dice remaining\n"
            "--------------------------------------------------------\n"
            "Final kept dice : [1, 1, 2, 2, one doll]\n"
            "Final kept total: 6\n"
            "Final dolls     : 1",
            output,
        )

    def test_choose_face_prefers_hitting_seven(self):
        self.assertEqual("4", choose_face_to_keep(["1", "1", "4"], kept_total=3))

    def test_choose_face_can_go_over_seven_to_stop(self):
        self.assertEqual("4", choose_face_to_keep(["4", "4", "one doll"], kept_total=5))

    def test_choose_face_cannot_reuse_reserved_pattern(self):
        self.assertEqual(
            "2",
            choose_face_to_keep(
                ["2", "2", "3", "3", "4"],
                kept_total=3,
                used_faces=["3"],
            ),
        )

    def test_turn_ends_when_no_new_pattern_is_available(self):
        rng = FixedRng([1, 1, 1, 1, 1, 2, 1])

        results = roll_dice_for_players(1, rng=rng)

        self.assertEqual(
            {
                "roll": ["1"],
                "kept_face": None,
                "kept_dice": [],
                "kept_total": 5,
                "remaining_dice": 1,
                "can_stop": False,
                "stopped": True,
                "ended_because_no_pattern": True,
            },
            results[0]["turns"][1],
        )
        self.assertEqual(["1", "1", "1", "1", "1"], results[0]["kept_dice"])
        self.assertEqual(0, results[0]["dolls_rolled"])
        self.assertEqual(0, results[0]["ignored_dice"])
        self.assertTrue(results[0]["ended_because_no_pattern"])

    def test_room_for_total_maps_results_to_doll_rooms(self):
        self.assertIsNone(room_for_total(6))
        self.assertEqual(7, room_for_total(7))
        self.assertEqual(8, room_for_total(8))
        self.assertEqual(9, room_for_total(9))
        self.assertEqual(10, room_for_total(10))
        self.assertEqual(11, room_for_total(11))
        self.assertEqual(11, room_for_total(14))

    def test_rooms_start_with_one_doll_in_rooms_seven_to_ten(self):
        self.assertEqual(
            {7: 1, 8: 1, 9: 1, 10: 1, 11: 0},
            create_doll_rooms(),
        )

    def test_fullest_adjustable_room_chooses_lowest_room_on_tie(self):
        rooms = create_doll_rooms()
        rooms[7] = 2
        rooms[8] = 3
        rooms[9] = 3
        rooms[10] = 1

        self.assertEqual(8, fullest_adjustable_room(rooms))

    def test_fullest_adjustable_rooms_returns_every_tied_fullest_room(self):
        rooms = create_doll_rooms()
        rooms[7] = 2
        rooms[8] = 5
        rooms[9] = 3
        rooms[10] = 5

        self.assertEqual([8, 10], fullest_adjustable_rooms(rooms))

    def test_adjusts_room_up_to_rolled_doll_count(self):
        rooms = create_doll_rooms()
        rooms[8] = 2
        turn_result = {
            "kept_total": 8,
            "kept_dice": ["one doll", "two dolls", "3", "3", "2"],
            "dolls_rolled": 4,
        }

        placement = place_dolls_for_turn(turn_result, INITIAL_PLAYER_DOLLS, rooms)

        self.assertEqual(4, rooms[8])
        self.assertEqual(8, placement["target_room"])
        self.assertEqual(2, placement["dolls_placed"])
        self.assertEqual(0, placement["dolls_returned"])
        self.assertEqual(8, placement["dolls_remaining"])

    def test_adjusts_room_down_and_returns_dolls_to_player(self):
        rooms = create_doll_rooms()
        rooms[9] = 2
        turn_result = {
            "kept_total": 9,
            "kept_dice": ["one doll", "4", "3", "2"],
            "dolls_rolled": 1,
        }

        placement = place_dolls_for_turn(turn_result, INITIAL_PLAYER_DOLLS, rooms)

        self.assertEqual(1, rooms[9])
        self.assertEqual(9, placement["target_room"])
        self.assertEqual(0, placement["dolls_placed"])
        self.assertEqual(1, placement["dolls_returned"])
        self.assertEqual(1, placement["overflow_dolls"])
        self.assertEqual(1, rooms[11])
        self.assertEqual(10, placement["dolls_remaining"])

    def test_total_below_seven_returns_all_dolls_from_fullest_room(self):
        rooms = create_doll_rooms()
        rooms[7] = 2
        rooms[8] = 5
        rooms[9] = 3
        rooms[10] = 5
        rooms[11] = 9
        turn_result = {
            "kept_total": 6,
            "kept_dice": ["one doll", "two dolls", "4", "2"],
            "dolls_rolled": 3,
        }

        placement = place_dolls_for_turn(turn_result, INITIAL_PLAYER_DOLLS, rooms)

        self.assertEqual(0, rooms[8])
        self.assertEqual(5, rooms[10])
        self.assertEqual(14, rooms[11])
        self.assertEqual(8, placement["target_room"])
        self.assertEqual(0, placement["dolls_placed"])
        self.assertEqual(5, placement["dolls_returned"])
        self.assertEqual(5, placement["overflow_dolls"])
        self.assertEqual(10, placement["dolls_remaining"])

    def test_total_below_seven_can_choose_tied_fullest_room(self):
        rooms = create_doll_rooms()
        rooms[7] = 2
        rooms[8] = 5
        rooms[9] = 3
        rooms[10] = 5
        turn_result = {
            "kept_total": 6,
            "kept_dice": ["4", "2"],
            "dolls_rolled": 0,
        }

        def choose_room(tied_rooms, **_context):
            self.assertEqual([8, 10], tied_rooms)
            return 10

        placement = place_dolls_for_turn(
            turn_result,
            INITIAL_PLAYER_DOLLS,
            rooms,
            choose_room=choose_room,
        )

        self.assertEqual(5, rooms[8])
        self.assertEqual(0, rooms[10])
        self.assertEqual(10, placement["target_room"])
        self.assertEqual((8, 10), placement["tied_rooms"])

    def test_total_eleven_or_more_adds_to_room_eleven(self):
        rooms = create_doll_rooms()
        rooms[11] = 2
        turn_result = {
            "kept_total": 12,
            "kept_dice": ["two dolls", "4", "4", "4"],
            "dolls_rolled": 2,
        }

        placement = place_dolls_for_turn(turn_result, INITIAL_PLAYER_DOLLS, rooms)

        self.assertEqual(4, rooms[11])
        self.assertEqual(11, placement["target_room"])
        self.assertEqual(2, placement["dolls_placed"])
        self.assertEqual(0, placement["dolls_returned"])

    def test_cannot_place_more_dolls_than_player_has(self):
        rooms = create_doll_rooms()
        turn_result = {
            "kept_total": 7,
            "kept_dice": ["two dolls", "two dolls", "one doll"],
            "dolls_rolled": 5,
        }

        placement = place_dolls_for_turn(turn_result, 3, rooms)

        self.assertEqual(4, rooms[7])
        self.assertEqual(3, placement["dolls_placed"])
        self.assertEqual(0, placement["dolls_returned"])
        self.assertEqual(0, placement["dolls_remaining"])

    def test_extra_dolls_above_ten_move_to_room_eleven(self):
        rooms = create_doll_rooms()

        overflow = move_extra_dolls_to_room_eleven(13, rooms)

        self.assertEqual(3, overflow["overflow_dolls"])
        self.assertEqual(10, overflow["dolls_remaining"])
        self.assertEqual(3, rooms[11])

    def test_extra_dolls_above_ten_move_for_all_players(self):
        rooms = create_doll_rooms()
        player_dolls = {1: 10, 2: 12, 3: 11}

        overflows = move_extra_dolls_for_all_players(player_dolls, rooms)

        self.assertEqual({2: 2, 3: 1}, overflows)
        self.assertEqual({1: 10, 2: 10, 3: 10}, player_dolls)
        self.assertEqual(3, rooms[11])

    def test_ones_can_gift_after_player_places_dolls(self):
        turn_result = {
            "kept_total": 8,
            "kept_dice": ["1", "1", "3", "3", "one doll", "two dolls"],
        }
        player_dolls = {1: 7, 2: 9}

        gift = give_dolls_for_ones(turn_result, 1, player_dolls, dolls_placed=3)

        self.assertEqual(2, gift["ones_rolled"])
        self.assertEqual(2, gift["gifted_dolls"])
        self.assertEqual(2, gift["gift_recipient"])
        self.assertEqual({2: 2}, gift["gift_recipients"])
        self.assertEqual({1: 5, 2: 11}, player_dolls)

    def test_ones_do_not_gift_when_no_dolls_were_placed(self):
        turn_result = {
            "kept_total": 9,
            "kept_dice": ["1", "4", "4"],
        }
        player_dolls = {1: 10, 2: 8}

        gift = give_dolls_for_ones(turn_result, 1, player_dolls, dolls_placed=0)

        self.assertEqual(1, gift["ones_rolled"])
        self.assertEqual(0, gift["gifted_dolls"])
        self.assertIsNone(gift["gift_recipient"])
        self.assertEqual({}, gift["gift_recipients"])
        self.assertEqual({1: 10, 2: 8}, player_dolls)

    def test_interactive_gift_can_choose_recipients_and_stop(self):
        turn_result = {
            "kept_total": 8,
            "kept_dice": ["1", "1", "1", "3", "3", "one doll"],
        }
        player_dolls = {1: 8, 2: 9, 3: 6}
        choices = iter([3, 2, None])

        def choose_gift_recipient(available_recipients, **context):
            self.assertEqual([2, 3], available_recipients)
            self.assertEqual(3, context["gift_limit"])
            return next(choices)

        gift = give_dolls_for_ones(
            turn_result,
            1,
            player_dolls,
            dolls_placed=2,
            choose_gift_recipient=choose_gift_recipient,
        )

        self.assertEqual(2, gift["gifted_dolls"])
        self.assertIsNone(gift["gift_recipient"])
        self.assertEqual({2: 1, 3: 1}, gift["gift_recipients"])
        self.assertEqual({1: 6, 2: 10, 3: 7}, player_dolls)

    def test_gift_after_placement_can_overflow_recipient_to_room_eleven(self):
        rooms = create_doll_rooms()
        rooms[8] = 1
        player_dolls = {1: 10, 2: 10}
        turn_result = {
            "kept_total": 8,
            "kept_dice": ["1", "1", "3", "3", "one doll", "two dolls"],
            "dolls_rolled": 3,
        }

        turn = resolve_turn_effects(1, turn_result, player_dolls, rooms)

        self.assertEqual(3, rooms[8])
        self.assertEqual(2, turn["dolls_placed"])
        self.assertEqual(2, turn["gifted_dolls"])
        self.assertEqual(2, turn["gift_recipient"])
        self.assertEqual({2: 2}, turn["gift_recipients"])
        self.assertEqual({2: 2}, turn["overflow_dolls_by_player"])
        self.assertEqual(2, rooms[11])
        self.assertEqual({1: 6, 2: 10}, player_dolls)
        self.assertEqual(6, turn["dolls_remaining"])

    def test_single_player_does_not_gift_for_ones(self):
        turn_result = {
            "kept_total": 8,
            "kept_dice": ["1", "1", "3", "3", "one doll"],
        }
        player_dolls = {1: 8}

        gift = give_dolls_for_ones(turn_result, 1, player_dolls, dolls_placed=1)

        self.assertEqual(2, gift["ones_rolled"])
        self.assertEqual(0, gift["gifted_dolls"])
        self.assertIsNone(gift["gift_recipient"])
        self.assertEqual({1: 8}, player_dolls)

    def test_game_turns_update_rooms_for_each_player(self):
        rng = FixedRng([
            5, 6, 4, 3, 2, 1,
            6, 4, 3, 2, 1,
            4, 3, 2, 1,
            3, 2, 1,
            6, 4, 4, 4, 1, 2,
            4, 4, 4, 1, 2,
        ])
        choices = iter(["one doll", "two dolls", "4", "3", "two dolls", "4"])

        def choose_face(roll, **_context):
            choice = next(choices)
            if choice not in roll:
                raise AssertionError(f"{choice} was not available in {roll}")
            return choice

        game_result = play_game_turns_for_players(2, rng=rng, choose_face=choose_face)

        self.assertEqual(3, game_result["rooms"][7])
        self.assertEqual(2, game_result["rooms"][11])
        self.assertEqual(8, game_result["players"][0]["dolls_remaining"])
        self.assertEqual(8, game_result["players"][1]["dolls_remaining"])

    def test_later_player_prompt_context_sees_updated_doll_state(self):
        rng = FixedRng([
            5, 6, 4, 3, 2, 1,
            6, 4, 3, 2, 1,
            4, 3, 2, 1,
            3, 2, 1,
            4, 4, 4, 1, 2, 3,
        ])
        choices = iter(["one doll", "two dolls", "4", "3", "4"])
        second_player_context = {}

        def choose_face(roll, **context):
            if context["player_index"] == 2 and not second_player_context:
                second_player_context.update(context)

            choice = next(choices)
            if choice not in roll:
                raise AssertionError(f"{choice} was not available in {roll}")
            return choice

        play_game_turns_for_players(2, rng=rng, choose_face=choose_face)

        self.assertEqual(8, second_player_context["player_dolls"][1])
        self.assertEqual(10, second_player_context["player_dolls"][2])
        self.assertEqual(3, second_player_context["rooms"][7])

    def test_game_ends_when_a_player_has_no_dolls(self):
        rng = FixedRng([
            6, 6, 6, 5, 4, 3,
            4, 4, 5,
            4, 4,
            4, 4, 4, 1, 1, 1,
            6, 6, 4, 4, 4, 1,
            4, 4, 4, 1,
        ])
        choices = iter(["two dolls", "one doll", "4", "4", "two dolls", "4"])

        def choose_face(roll, **_context):
            choice = next(choices)
            if choice not in roll:
                raise AssertionError(f"{choice} was not available in {roll}")
            return choice

        game_result = play_game(2, rng=rng, choose_face=choose_face)

        self.assertEqual(1, game_result["winner"])
        self.assertEqual(3, len(game_result["turns"]))
        self.assertEqual(4, game_result["turns"][0]["dolls_remaining"])
        self.assertEqual(10, game_result["turns"][1]["starting_dolls"])
        self.assertEqual(10, game_result["turns"][1]["dolls_remaining"])
        self.assertEqual(0, game_result["turns"][2]["dolls_remaining"])
        self.assertEqual(1, game_result["rooms"][7])
        self.assertEqual(7, game_result["rooms"][8])
        self.assertEqual(4, game_result["rooms"][11])
        self.assertEqual(0, game_result["player_dolls"][1])
        self.assertEqual(10, game_result["player_dolls"][2])

        output = format_game_result(game_result)
        self.assertIn("Turn 1 - Player 1 result", output)
        self.assertIn("Turn 3 - Player 1 result", output)
        self.assertIn("Winner: Player 1", output)

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
            used_faces=["3"],
            player_dolls={1: 10, 2: 8},
            rooms={7: 1, 8: 0, 9: 2, 10: 0, 11: 3},
            input_fn=fake_input,
            output_fn=output.append,
        )

        self.assertEqual("1", result)
        self.assertEqual(["Keep pattern > "], prompts)
        self.assertIn("Player 2 - choose a pattern", output)
        self.assertIn("Player dolls:", output)
        self.assertIn("  Player 1: 10 dolls", output)
        self.assertIn("  Player 2: 8 dolls", output)
        self.assertIn("Doll rooms:", output)
        self.assertIn("  Room 7: 1 dolls", output)
        self.assertIn("  Room 11: 3 dolls", output)
        self.assertIn("Kept dice        : [3]", output)
        self.assertIn("Reserved patterns: [3]", output)
        self.assertIn("Roll             : [1, 1, 3, one doll]", output)
        self.assertIn("Dolls rolled     : 1", output)
        self.assertIn("  [b] 1 x2 | adds 2 | total -> 4", output)
        self.assertNotIn("  [c] 3 x1 | adds 3 | total -> 5", output)

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
                player_dolls={1: 8, 2: 10},
                rooms={7: 0, 8: 2, 9: 0, 10: 0, 11: 1},
                input_fn=fake_input,
                output_fn=output.append,
            )
        )
        self.assertEqual(["Stop? > "], prompts)
        self.assertIn("Player 1 - stop check", output)
        self.assertIn("  Player 1: 8 dolls", output)
        self.assertIn("  Player 2: 10 dolls", output)
        self.assertIn("  Room 8: 2 dolls", output)
        self.assertIn("Kept dice : [4, 4]", output)
        self.assertIn("Kept total: 8", output)
        self.assertIn("Remaining : 2 dice", output)
        self.assertIn("Stop now and ignore the remaining dice? [y/n]", output)

    def test_choose_room_interactively_accepts_lettered_choice(self):
        prompts = []
        output = []

        def fake_input(prompt):
            prompts.append(prompt)
            return "b"

        result = choose_room_interactively(
            [8, 10],
            player_index=1,
            turn_result={"kept_total": 6, "kept_dice": ["4", "2"]},
            player_dolls={1: 10, 2: 8},
            rooms={7: 1, 8: 5, 9: 3, 10: 5, 11: 0},
            input_fn=fake_input,
            output_fn=output.append,
        )

        self.assertEqual(10, result)
        self.assertEqual(["Room > "], prompts)
        self.assertIn("Player 1 - choose a room", output)
        self.assertIn("Total is 6 or less. Take all dolls from one fullest room.", output)
        self.assertIn("  [a] Room 8: 5 dolls", output)
        self.assertIn("  [b] Room 10: 5 dolls", output)

    def test_choose_gift_recipient_interactively_can_stop(self):
        prompts = []
        output = []

        def fake_input(prompt):
            prompts.append(prompt)
            return "a"

        result = choose_gift_recipient_interactively(
            [2, 3],
            gift_number=1,
            gift_limit=2,
            player_index=1,
            turn_result={"kept_dice": ["1", "1", "3", "3"]},
            player_dolls={1: 8, 2: 10, 3: 6},
            rooms={7: 1, 8: 2, 9: 1, 10: 1, 11: 0},
            input_fn=fake_input,
            output_fn=output.append,
        )

        self.assertIsNone(result)
        self.assertEqual(["Gift doll > "], prompts)
        self.assertIn("Player 1 - give a doll", output)
        self.assertIn("Giving is optional. Choose a player or stop giving.", output)
        self.assertIn("  [a] Stop giving", output)
        self.assertIn("  [b] Player 2", output)
        self.assertIn("  [c] Player 3", output)

    def test_choose_gift_recipient_interactively_accepts_player_letter(self):
        def fake_input(_prompt):
            return "c"

        result = choose_gift_recipient_interactively(
            [2, 3],
            gift_number=1,
            gift_limit=2,
            input_fn=fake_input,
            output_fn=lambda _message: None,
        )

        self.assertEqual(3, result)

    def test_two_players_can_use_interactive_choices(self):
        rng = FixedRng([
            3, 3, 1, 2, 5, 6,
            4, 4, 5, 6,
            1, 2, 3, 4, 5, 6,
            4, 4, 4, 4, 4,
        ])
        choices = iter(["e", "c", "y", "e", "a"])

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
        self.assertEqual(["3", "4", "4", "4", "4", "4"], results[1]["kept_dice"])
        self.assertEqual(23, results[1]["kept_total"])
        self.assertEqual(0, results[1]["ignored_dice"])

    def test_requires_at_least_one_player(self):
        with self.assertRaises(ValueError):
            roll_dice_for_players(0)


if __name__ == "__main__":
    unittest.main()
