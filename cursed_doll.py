import argparse
import random

from player_turn import (
    choose_face_interactively,
    choose_face_to_keep,
    choose_stop_interactively,
    format_rolls,
    roll_dice_for_players,
    should_stop_automatically,
)


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
    if args.interactive:
        print()
    print(format_rolls(rolls))


if __name__ == "__main__":
    main()
