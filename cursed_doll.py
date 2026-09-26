import argparse
from collections import Counter
import random


DEFAULT_DICE_COUNT = 6
DEFAULT_DICE_SIDES = 6


def validate_dice_settings(dice_count, sides):
    if dice_count < 1:
        raise ValueError("dice_count must be at least 1")
    if sides < 2:
        raise ValueError("sides must be at least 2")


def choose_number_to_keep(roll):
    if not roll:
        raise ValueError("roll must include at least one die")

    counts = Counter(roll)
    best_count = max(counts.values())
    return min(number for number, count in counts.items() if count == best_count)


def roll_until_all_dice_are_kept(dice_count=DEFAULT_DICE_COUNT, sides=DEFAULT_DICE_SIDES, rng=None):
    validate_dice_settings(dice_count, sides)

    roller = rng or random
    remaining_dice = dice_count
    kept_dice = []
    turns = []

    while remaining_dice > 0:
        roll = [roller.randint(1, sides) for _ in range(remaining_dice)]
        kept_number = choose_number_to_keep(roll)
        kept_count = roll.count(kept_number)
        kept_this_turn = [kept_number] * kept_count

        kept_dice.extend(kept_this_turn)
        remaining_dice -= kept_count
        turns.append(
            {
                "roll": roll,
                "kept_number": kept_number,
                "kept_dice": kept_this_turn,
                "remaining_dice": remaining_dice,
            }
        )

    return {
        "turns": turns,
        "kept_dice": kept_dice,
    }


def roll_dice_for_players(player_count, dice_count=DEFAULT_DICE_COUNT, sides=DEFAULT_DICE_SIDES, rng=None):
    if player_count < 1:
        raise ValueError("player_count must be at least 1")
    validate_dice_settings(dice_count, sides)

    roller = rng or random
    return [
        roll_until_all_dice_are_kept(dice_count=dice_count, sides=sides, rng=roller)
        for _ in range(player_count)
    ]


def format_rolls(player_results):
    lines = []
    for player_index, result in enumerate(player_results, start=1):
        lines.append(f"Player {player_index}:")
        for turn_index, turn in enumerate(result["turns"], start=1):
            roll = ", ".join(str(value) for value in turn["roll"])
            kept = ", ".join(str(value) for value in turn["kept_dice"])
            remaining_label = "die" if turn["remaining_dice"] == 1 else "dice"
            lines.append(
                f"  Roll {turn_index}: rolled [{roll}], kept [{kept}], "
                f"{turn['remaining_dice']} {remaining_label} remaining"
            )

        final_result = ", ".join(str(value) for value in result["kept_dice"])
        lines.append(f"  Final kept dice: {final_result}")
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Roll six dice for each player, keeping matching dice each turn."
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
    return parser.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.seed) if args.seed is not None else random
    rolls = roll_dice_for_players(args.players, rng=rng)
    print(format_rolls(rolls))


if __name__ == "__main__":
    main()
