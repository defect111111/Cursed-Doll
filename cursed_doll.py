import argparse
from collections import Counter
import random


DEFAULT_DICE_COUNT = 6
TARGET_KEPT_TOTAL = 7
DIE_FACES = (
    ("1", 1),
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("one doll", 0),
    ("two dolls", 0),
)
FACE_VALUES = dict(DIE_FACES)


def validate_dice_settings(dice_count):
    if dice_count < 1:
        raise ValueError("dice_count must be at least 1")


def choose_face_to_keep(roll, kept_total=0, **_context):
    if not roll:
        raise ValueError("roll must include at least one die")

    counts = Counter(roll)
    stopping_faces = [
        face
        for face, count in counts.items()
        if kept_total + FACE_VALUES[face] * count >= TARGET_KEPT_TOTAL
    ]
    if stopping_faces:
        return min(
            stopping_faces,
            key=lambda face: (kept_total + FACE_VALUES[face] * counts[face], FACE_VALUES[face], face),
        )

    possible_faces = [
        face
        for face, count in counts.items()
        if kept_total + FACE_VALUES[face] * count < TARGET_KEPT_TOTAL
    ]
    if not possible_faces:
        possible_faces = list(counts.keys())

    best_count = max(counts[face] for face in possible_faces)
    tied_faces = [face for face in possible_faces if counts[face] == best_count]
    return min(tied_faces, key=lambda face: (FACE_VALUES[face], face))


def format_dice(dice):
    return ", ".join(str(value) for value in dice)


def choose_face_interactively(
    roll,
    kept_total=0,
    player_index=None,
    kept_dice=None,
    input_fn=input,
    output_fn=print,
):
    counts = Counter(roll)
    choices = sorted(counts, key=lambda face: (FACE_VALUES[face], face))
    kept_dice = kept_dice or []

    if player_index is not None:
        output_fn(f"Player {player_index}")
    output_fn(f"Kept so far: [{format_dice(kept_dice)}]")
    output_fn(f"Current kept total: {kept_total}")
    output_fn(f"Rolled: {format_dice(roll)}")
    output_fn("Choose a face to keep:")
    choice_labels = [chr(ord("a") + index) for index in range(len(choices))]
    for label, face in zip(choice_labels, choices):
        count = counts[face]
        score = FACE_VALUES[face] * count
        projected_total = kept_total + score
        output_fn(
            f"  {label}. {face} x{count} "
            f"(adds {score}, total would be {projected_total})"
        )

    while True:
        raw_choice = input_fn("> ").strip().lower()
        if raw_choice in choice_labels:
            return choices[choice_labels.index(raw_choice)]

        if raw_choice in choices:
            return raw_choice

        output_fn("Enter a listed letter or face name.")


def should_stop_automatically(kept_total, remaining_dice, **_context):
    return kept_total >= TARGET_KEPT_TOTAL


def choose_stop_interactively(
    kept_total,
    remaining_dice,
    player_index=None,
    kept_dice=None,
    input_fn=input,
    output_fn=print,
):
    if kept_total < TARGET_KEPT_TOTAL or remaining_dice == 0:
        return False

    kept_dice = kept_dice or []
    remaining_label = "die" if remaining_dice == 1 else "dice"
    if player_index is not None:
        output_fn(f"Player {player_index}")
    output_fn(f"Kept so far: [{format_dice(kept_dice)}]")
    output_fn(
        f"Kept total is {kept_total}. Stop and ignore {remaining_dice} {remaining_label}? [y/n]"
    )
    while True:
        raw_choice = input_fn("> ").strip().lower()
        if raw_choice in ("y", "yes"):
            return True
        if raw_choice in ("n", "no"):
            return False

        output_fn("Enter y or n.")


def roll_dice(dice_count, rng):
    return [DIE_FACES[rng.randint(1, len(DIE_FACES)) - 1][0] for _ in range(dice_count)]


def roll_until_done(
    dice_count=DEFAULT_DICE_COUNT,
    rng=None,
    choose_face=choose_face_to_keep,
    should_stop=should_stop_automatically,
    player_index=None,
):
    validate_dice_settings(dice_count)

    roller = rng or random
    remaining_dice = dice_count
    kept_dice = []
    kept_total = 0
    turns = []
    stopped = False

    while remaining_dice > 0 and not stopped:
        roll = roll_dice(remaining_dice, roller)
        kept_face = choose_face(
            roll,
            kept_total=kept_total,
            player_index=player_index,
            kept_dice=tuple(kept_dice),
        )
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
            }
        )

    return {
        "turns": turns,
        "kept_dice": kept_dice,
        "kept_total": kept_total,
        "ignored_dice": remaining_dice if stopped else 0,
        "stopped": stopped,
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


def format_rolls(player_results):
    lines = []
    for player_index, result in enumerate(player_results, start=1):
        lines.append(f"Player {player_index}:")
        for turn_index, turn in enumerate(result["turns"], start=1):
            roll = format_dice(turn["roll"])
            kept = format_dice(turn["kept_dice"])
            remaining_label = "die" if turn["remaining_dice"] == 1 else "dice"
            lines.append(
                f"  Roll {turn_index}: rolled [{roll}], kept [{kept}], "
                f"total {turn['kept_total']}, {turn['remaining_dice']} {remaining_label} remaining"
            )

        final_result = format_dice(result["kept_dice"])
        lines.append(f"  Final kept dice: {final_result}")
        lines.append(f"  Final kept total: {result['kept_total']}")
        if result["ignored_dice"]:
            ignored_label = "die" if result["ignored_dice"] == 1 else "dice"
            lines.append(
                f"  Stopped at {result['kept_total']} and ignored "
                f"{result['ignored_dice']} {ignored_label}"
            )
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Roll six custom dice for each player, stopping when kept dice total is at least 7."
    )
    parser.add_argument(
        "players",
        type=int,
        help="Number of players rolling dice.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for repeatable results.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Choose which face to keep after every roll.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.seed) if args.seed is not None else random
    choose_face = choose_face_interactively if args.interactive else choose_face_to_keep
    should_stop = choose_stop_interactively if args.interactive else should_stop_automatically
    rolls = roll_dice_for_players(
        args.players,
        rng=rng,
        choose_face=choose_face,
        should_stop=should_stop,
    )
    print(format_rolls(rolls))


if __name__ == "__main__":
    main()
