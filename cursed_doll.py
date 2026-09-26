import argparse
import random


DEFAULT_DICE_COUNT = 6
DEFAULT_DICE_SIDES = 6


def roll_dice_for_players(player_count, dice_count=DEFAULT_DICE_COUNT, sides=DEFAULT_DICE_SIDES, rng=None):
    if player_count < 1:
        raise ValueError("player_count must be at least 1")
    if dice_count < 1:
        raise ValueError("dice_count must be at least 1")
    if sides < 2:
        raise ValueError("sides must be at least 2")

    roller = rng or random
    return [
        [roller.randint(1, sides) for _ in range(dice_count)]
        for _ in range(player_count)
    ]


def format_rolls(rolls):
    lines = []
    for player_index, dice in enumerate(rolls, start=1):
        result = ", ".join(str(value) for value in dice)
        lines.append(f"Player {player_index}: {result}")
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Roll six dice for each player.")
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
