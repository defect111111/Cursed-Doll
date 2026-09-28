from collections import Counter
import random

from cursed_doll.dice import DEFAULT_DICE_COUNT, DIE_FACES, FACE_VALUES, TARGET_KEPT_TOTAL, count_dolls, roll_dice
from cursed_doll.game import (
    ADJUSTABLE_ROOMS,
    DOLL_ROOMS,
    create_doll_rooms,
    fullest_adjustable_rooms,
    move_extra_dolls_to_room_eleven,
    place_dolls_for_turn,
    room_for_total,
)


FACE_NAMES = tuple(face for face, _value in DIE_FACES)
FACE_TO_ACTION = {face: index for index, face in enumerate(FACE_NAMES)}
ACTION_TO_FACE = {index: face for face, index in FACE_TO_ACTION.items()}

ACTION_CONTINUE = 6
ACTION_STOP = 7
ACTION_ROOM_7 = 8
ACTION_ROOM_8 = 9
ACTION_ROOM_9 = 10
ACTION_ROOM_10 = 11
ACTION_GIVE_DOLL = 12
ACTION_STOP_GIVING = 13
ACTION_COUNT = 14

ROOM_TO_ACTION = {
    7: ACTION_ROOM_7,
    8: ACTION_ROOM_8,
    9: ACTION_ROOM_9,
    10: ACTION_ROOM_10,
}
ACTION_TO_ROOM = {action: room for room, action in ROOM_TO_ACTION.items()}

PHASES = ("choose_face", "stop_check", "choose_room", "gift", "done")


class TurnEnv:
    """Single-turn environment for training a local turn optimizer."""

    def __init__(self, rng=None, allow_gifts=True, randomize_start=True):
        self.rng = rng or random.Random()
        self.allow_gifts = allow_gifts
        self.randomize_start = randomize_start
        self.reset()

    def reset(self, player_dolls=None, rooms=None, seed=None):
        if seed is not None:
            self.rng.seed(seed)

        if rooms is None:
            rooms = self._random_rooms() if self.randomize_start else create_doll_rooms()
        if player_dolls is None:
            player_dolls = (
                self.rng.randint(1, 10) if self.randomize_start else 10
            )

        self.rooms = {room: int(rooms[room]) for room in DOLL_ROOMS}
        self.player_dolls = int(player_dolls)
        self.starting_dolls = int(player_dolls)
        self.remaining_dice = DEFAULT_DICE_COUNT
        self.kept_dice = []
        self.kept_total = 0
        self.used_faces = []
        self.turn_rolls = []
        self.current_roll = []
        self.pending_turn_result = None
        self.pending_placement = None
        self.gift_remaining = 0
        self.gifted_dolls = 0
        self.phase = "choose_face"
        self.done = False
        self.last_reward = 0.0
        self.final_info = None
        self._roll_for_choice()
        return self.observation()

    @property
    def observation_size(self):
        return len(self.observation())

    def observation(self):
        roll_counts = self._face_counts(self.current_roll)
        kept_counts = self._face_counts(self.kept_dice)
        used_mask = [1.0 if face in self.used_faces else 0.0 for face in FACE_NAMES]
        phase_mask = [1.0 if self.phase == phase else 0.0 for phase in PHASES]
        return [
            self.player_dolls / 10.0,
            *[self.rooms[room] / 10.0 for room in DOLL_ROOMS],
            *[count / DEFAULT_DICE_COUNT for count in roll_counts],
            *[count / DEFAULT_DICE_COUNT for count in kept_counts],
            *used_mask,
            self.kept_total / 24.0,
            self.remaining_dice / DEFAULT_DICE_COUNT,
            count_dolls(self.kept_dice) / 12.0,
            *phase_mask,
        ]

    def legal_action_mask(self):
        mask = [False] * ACTION_COUNT
        if self.phase == "choose_face":
            for face in self._available_faces():
                mask[FACE_TO_ACTION[face]] = True
        elif self.phase == "stop_check":
            mask[ACTION_CONTINUE] = True
            mask[ACTION_STOP] = True
        elif self.phase == "choose_room":
            for room in self.tied_rooms:
                mask[ROOM_TO_ACTION[room]] = True
        elif self.phase == "gift":
            mask[ACTION_STOP_GIVING] = True
            if self.gift_remaining > 0 and self.player_dolls > 0:
                mask[ACTION_GIVE_DOLL] = True
        return mask

    def step(self, action):
        if self.done:
            raise ValueError("Turn is already done. Call reset() before stepping again.")
        if not self.legal_action_mask()[action]:
            raise ValueError(f"Action {action} is not legal during phase {self.phase}.")

        if self.phase == "choose_face":
            self._choose_face(ACTION_TO_FACE[action])
        elif self.phase == "stop_check":
            self._choose_stop(action == ACTION_STOP)
        elif self.phase == "choose_room":
            self._apply_placement(ACTION_TO_ROOM[action])
        elif self.phase == "gift":
            if action == ACTION_GIVE_DOLL:
                self._give_doll()
            else:
                self._complete_turn()

        return self.observation(), self.last_reward, self.done, self.info()

    def info(self):
        if self.final_info is not None:
            return dict(self.final_info)
        return {
            "phase": self.phase,
            "player_dolls": self.player_dolls,
            "rooms": dict(self.rooms),
            "kept_total": self.kept_total,
            "kept_dice": list(self.kept_dice),
            "dolls_rolled": count_dolls(self.kept_dice),
        }

    def _random_rooms(self):
        rooms = create_doll_rooms()
        for room in ADJUSTABLE_ROOMS:
            rooms[room] = self.rng.randint(0, 8)
        rooms[11] = self.rng.randint(0, 16)
        return rooms

    def _face_counts(self, dice):
        counts = Counter(dice)
        return [counts[face] for face in FACE_NAMES]

    def _available_faces(self):
        used_faces = set(self.used_faces)
        return [face for face in Counter(self.current_roll) if face not in used_faces]

    def _roll_for_choice(self):
        self.current_roll = roll_dice(self.remaining_dice, self.rng)
        if not self._available_faces():
            self.turn_rolls.append(
                {
                    "roll": list(self.current_roll),
                    "kept_face": None,
                    "kept_dice": [],
                    "kept_total": self.kept_total,
                    "remaining_dice": self.remaining_dice,
                    "can_stop": self.kept_total >= TARGET_KEPT_TOTAL,
                    "stopped": True,
                    "ended_because_no_pattern": True,
                }
            )
            self._finish_turn(stopped=True, ended_because_no_pattern=True)
            return
        self.phase = "choose_face"

    def _choose_face(self, face):
        kept_count = self.current_roll.count(face)
        kept_this_turn = [face] * kept_count
        self.kept_dice.extend(kept_this_turn)
        self.used_faces.append(face)
        self.kept_total += FACE_VALUES[face] * kept_count
        self.remaining_dice -= kept_count
        can_stop = self.kept_total >= TARGET_KEPT_TOTAL
        stopped = can_stop and self.remaining_dice == 0
        self.turn_rolls.append(
            {
                "roll": list(self.current_roll),
                "kept_face": face,
                "kept_dice": kept_this_turn,
                "kept_total": self.kept_total,
                "remaining_dice": self.remaining_dice,
                "can_stop": can_stop,
                "stopped": stopped,
                "ended_because_no_pattern": False,
            }
        )

        if self.remaining_dice == 0:
            self._finish_turn(stopped=stopped, ended_because_no_pattern=False)
        elif can_stop:
            self.phase = "stop_check"
        else:
            self._roll_for_choice()

    def _choose_stop(self, stop):
        if stop:
            self.turn_rolls[-1]["stopped"] = True
            self._finish_turn(stopped=True, ended_because_no_pattern=False)
        else:
            self._roll_for_choice()

    def _current_turn_result(self, stopped=False, ended_because_no_pattern=False):
        return {
            "turns": list(self.turn_rolls),
            "kept_dice": list(self.kept_dice),
            "kept_total": self.kept_total,
            "dolls_rolled": count_dolls(self.kept_dice),
            "ignored_dice": (
                self.remaining_dice
                if stopped and not ended_because_no_pattern
                else 0
            ),
            "stopped": stopped,
            "ended_because_no_pattern": ended_because_no_pattern,
        }

    def _finish_turn(self, stopped=False, ended_because_no_pattern=False):
        self.pending_turn_result = self._current_turn_result(
            stopped=stopped,
            ended_because_no_pattern=ended_because_no_pattern,
        )
        target_room = room_for_total(self.pending_turn_result["kept_total"])
        if target_room is None:
            self.tied_rooms = fullest_adjustable_rooms(self.rooms)
            if len(self.tied_rooms) > 1:
                self.phase = "choose_room"
                return
            target_room = self.tied_rooms[0]
        self._apply_placement(target_room)

    def _apply_placement(self, chosen_room):
        def choose_room(_tied_rooms, **_context):
            return chosen_room

        placement = place_dolls_for_turn(
            self.pending_turn_result,
            self.player_dolls,
            self.rooms,
            apply_overflow=False,
            choose_room=choose_room,
            player_index=1,
            player_dolls_by_player={1: self.player_dolls},
        )
        self.player_dolls = placement["dolls_remaining"]
        self.pending_placement = placement
        self.gift_remaining = min(
            self.pending_turn_result["kept_dice"].count("1"),
            self.player_dolls,
        )
        if self.allow_gifts and placement["dolls_placed"] > 0 and self.gift_remaining > 0:
            self.phase = "gift"
        else:
            self._complete_turn()

    def _give_doll(self):
        self.player_dolls -= 1
        self.gift_remaining -= 1
        self.gifted_dolls += 1
        if self.gift_remaining <= 0 or self.player_dolls <= 0:
            self._complete_turn()

    def _complete_turn(self):
        overflow = move_extra_dolls_to_room_eleven(self.player_dolls, self.rooms)
        self.player_dolls = overflow["dolls_remaining"]
        self.phase = "done"
        self.done = True
        self.last_reward = float(self.starting_dolls - self.player_dolls)
        self.final_info = {
            "phase": self.phase,
            "reward": self.last_reward,
            "starting_dolls": self.starting_dolls,
            "player_dolls": self.player_dolls,
            "rooms": dict(self.rooms),
            "turn_result": self.pending_turn_result,
            "placement": dict(self.pending_placement),
            "gifted_dolls": self.gifted_dolls,
            "overflow_dolls": overflow["overflow_dolls"],
        }
