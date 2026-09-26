from collections import Counter
import random

from dice import (
    DEFAULT_DICE_COUNT,
    FACE_VALUES,
    TARGET_KEPT_TOTAL,
    available_faces_for_roll,
    count_dolls,
    format_dice,
    roll_dice,
    validate_dice_settings,
)


DIVIDER = "-" * 56
HEADER_DIVIDER = "=" * 56


def format_room_state(rooms):
    if not rooms:
        return []
    return [f"  Room {room}: {rooms[room]} dolls" for room in sorted(rooms)]


def format_player_doll_state(player_dolls):
    if player_dolls is None:
        return []
    if isinstance(player_dolls, dict):
        return [
            f"  Player {player_index}: {player_dolls[player_index]} dolls"
            for player_index in sorted(player_dolls)
        ]
    return [f"  Current player: {player_dolls} dolls"]


def output_game_state(player_dolls, rooms, output_fn):
    player_lines = format_player_doll_state(player_dolls)
    room_lines = format_room_state(rooms)

    if player_lines:
        output_fn("Player dolls:")
        for line in player_lines:
            output_fn(line)

    if room_lines:
        output_fn("Doll rooms:")
        for line in room_lines:
            output_fn(line)

    if player_lines or room_lines:
        output_fn(DIVIDER)


def choose_face_to_keep(roll, kept_total=0, used_faces=None, **_context):
    available_faces = available_faces_for_roll(roll, used_faces=used_faces)
    if not available_faces:
        return None

    counts = Counter(roll)
    stopping_faces = [
        face
        for face in available_faces
        for count in [counts[face]]
        if kept_total + FACE_VALUES[face] * count >= TARGET_KEPT_TOTAL
    ]
    if stopping_faces:
        return min(
            stopping_faces,
            key=lambda face: (
                kept_total + FACE_VALUES[face] * counts[face],
                FACE_VALUES[face],
                face,
            ),
        )

    possible_faces = [
        face
        for face in available_faces
        for count in [counts[face]]
        if kept_total + FACE_VALUES[face] * count < TARGET_KEPT_TOTAL
    ]
    if not possible_faces:
        possible_faces = available_faces

    best_count = max(counts[face] for face in possible_faces)
    tied_faces = [face for face in possible_faces if counts[face] == best_count]
    return min(tied_faces, key=lambda face: (FACE_VALUES[face], face))


def choose_face_interactively(
    roll,
    kept_total=0,
    player_index=None,
    kept_dice=None,
    used_faces=None,
    player_dolls=None,
    rooms=None,
    input_fn=input,
    output_fn=print,
):
    counts = Counter(roll)
    choices = sorted(
        available_faces_for_roll(roll, used_faces=used_faces),
        key=lambda face: (FACE_VALUES[face], face),
    )
    kept_dice = kept_dice or []
    used_faces = used_faces or []

    output_fn("")
    output_fn(HEADER_DIVIDER)
    if player_index is not None:
        output_fn(f"Player {player_index} - choose a pattern")
    else:
        output_fn("Choose a pattern")
    output_fn(DIVIDER)
    output_game_state(player_dolls, rooms, output_fn)
    output_fn(f"Kept dice        : [{format_dice(kept_dice)}]")
    output_fn(f"Reserved patterns: [{format_dice(used_faces)}]")
    output_fn(f"Kept total       : {kept_total}")
    output_fn(f"Roll             : [{format_dice(roll)}]")
    output_fn(f"Dolls rolled     : {count_dolls(roll)}")
    if not choices:
        output_fn("No new pattern is available. Turn ends.")
        return None

    output_fn(DIVIDER)
    output_fn("Available choices:")
    choice_labels = [chr(ord("a") + index) for index in range(len(choices))]
    for label, face in zip(choice_labels, choices):
        count = counts[face]
        score = FACE_VALUES[face] * count
        projected_total = kept_total + score
        output_fn(
            f"  [{label}] {face} x{count} | adds {score} | total -> {projected_total}"
        )

    while True:
        raw_choice = input_fn("Keep pattern > ").strip().lower()
        if raw_choice in choice_labels:
            return choices[choice_labels.index(raw_choice)]

        if raw_choice in choices:
            return raw_choice

        output_fn("Please enter a listed letter or face name.")


def should_stop_automatically(kept_total, remaining_dice, **_context):
    return kept_total >= TARGET_KEPT_TOTAL


def choose_stop_interactively(
    kept_total,
    remaining_dice,
    player_index=None,
    kept_dice=None,
    player_dolls=None,
    rooms=None,
    input_fn=input,
    output_fn=print,
):
    if kept_total < TARGET_KEPT_TOTAL or remaining_dice == 0:
        return False

    kept_dice = kept_dice or []
    remaining_label = "die" if remaining_dice == 1 else "dice"
    output_fn("")
    output_fn(HEADER_DIVIDER)
    if player_index is not None:
        output_fn(f"Player {player_index} - stop check")
    else:
        output_fn("Stop check")
    output_fn(DIVIDER)
    output_game_state(player_dolls, rooms, output_fn)
    output_fn(f"Kept dice : [{format_dice(kept_dice)}]")
    output_fn(f"Kept total: {kept_total}")
    output_fn(
        f"Remaining : {remaining_dice} {remaining_label}"
    )
    output_fn(
        f"Stop now and ignore the remaining {remaining_label}? [y/n]"
    )
    while True:
        raw_choice = input_fn("Stop? > ").strip().lower()
        if raw_choice in ("y", "yes"):
            return True
        if raw_choice in ("n", "no"):
            return False

        output_fn("Please enter y or n.")


def roll_until_done(
    dice_count=DEFAULT_DICE_COUNT,
    rng=None,
    choose_face=choose_face_to_keep,
    should_stop=should_stop_automatically,
    player_index=None,
    player_dolls=None,
    rooms=None,
):
    validate_dice_settings(dice_count)

    roller = rng or random
    remaining_dice = dice_count
    kept_dice = []
    kept_total = 0
    turns = []
    stopped = False
    ended_because_no_pattern = False

    while remaining_dice > 0 and not stopped:
        roll = roll_dice(remaining_dice, roller)
        used_faces = tuple(dict.fromkeys(turn["kept_face"] for turn in turns if turn["kept_face"]))
        kept_face = choose_face(
            roll,
            kept_total=kept_total,
            player_index=player_index,
            kept_dice=tuple(kept_dice),
            used_faces=used_faces,
            player_dolls=player_dolls,
            rooms=rooms,
        )
        if kept_face is None:
            ended_because_no_pattern = True
            turns.append(
                {
                    "roll": roll,
                    "kept_face": None,
                    "kept_dice": [],
                    "kept_total": kept_total,
                    "remaining_dice": remaining_dice,
                    "can_stop": kept_total >= TARGET_KEPT_TOTAL,
                    "stopped": True,
                    "ended_because_no_pattern": True,
                }
            )
            stopped = True
            break

        kept_count = roll.count(kept_face)
        kept_this_turn = [kept_face] * kept_count

        kept_dice.extend(kept_this_turn)
        kept_total += FACE_VALUES[kept_face] * kept_count
        remaining_dice -= kept_count
        can_stop = kept_total >= TARGET_KEPT_TOTAL
        stopped = can_stop and (
            remaining_dice == 0
            or should_stop(
                kept_total,
                remaining_dice,
                player_index=player_index,
                kept_dice=tuple(kept_dice),
                player_dolls=player_dolls,
                rooms=rooms,
            )
        )
        turns.append(
            {
                "roll": roll,
                "kept_face": kept_face,
                "kept_dice": kept_this_turn,
                "kept_total": kept_total,
                "remaining_dice": remaining_dice,
                "can_stop": can_stop,
                "stopped": stopped,
                "ended_because_no_pattern": False,
            }
        )

    return {
        "turns": turns,
        "kept_dice": kept_dice,
        "kept_total": kept_total,
        "dolls_rolled": count_dolls(kept_dice),
        "ignored_dice": remaining_dice if stopped and not ended_because_no_pattern else 0,
        "stopped": stopped,
        "ended_because_no_pattern": ended_because_no_pattern,
    }


def roll_dice_for_players(
    player_count,
    dice_count=DEFAULT_DICE_COUNT,
    rng=None,
    choose_face=choose_face_to_keep,
    should_stop=should_stop_automatically,
):
    if player_count < 1:
        raise ValueError("player_count must be at least 1")
    validate_dice_settings(dice_count)

    roller = rng or random
    results = []
    for player_index in range(1, player_count + 1):
        results.append(
            roll_until_done(
                dice_count=dice_count,
                rng=roller,
                choose_face=choose_face,
                should_stop=should_stop,
                player_index=player_index,
            )
        )
    return results


def format_rolls(player_results, labels=None):
    lines = []
    for result_index, result in enumerate(player_results, start=1):
        if lines:
            lines.append("")
        lines.append(HEADER_DIVIDER)
        label = labels[result_index - 1] if labels else f"Player {result_index}"
        lines.append(f"{label} result")
        lines.append(DIVIDER)
        for turn_index, turn in enumerate(result["turns"], start=1):
            roll = format_dice(turn["roll"])
            kept = format_dice(turn["kept_dice"])
            remaining_label = "die" if turn["remaining_dice"] == 1 else "dice"
            lines.append(
                f"Roll {turn_index}: rolled [{roll}] | kept [{kept}] | "
                f"total {turn['kept_total']} | {turn['remaining_dice']} {remaining_label} remaining"
            )
            if turn["kept_face"] is None:
                lines[-1] += " | no new pattern; turn ends"

        final_result = format_dice(result["kept_dice"])
        lines.append(DIVIDER)
        lines.append(f"Final kept dice : [{final_result}]")
        lines.append(f"Final kept total: {result['kept_total']}")
        lines.append(f"Final dolls     : {result.get('dolls_rolled', count_dolls(result['kept_dice']))}")
        if result["ignored_dice"]:
            ignored_label = "die" if result["ignored_dice"] == 1 else "dice"
            lines.append(
                f"Stopped at {result['kept_total']} and ignored "
                f"{result['ignored_dice']} {ignored_label}"
            )
        if result.get("ended_because_no_pattern", False):
            lines.append("Turn ended because no new pattern was available")
    return "\n".join(lines)
