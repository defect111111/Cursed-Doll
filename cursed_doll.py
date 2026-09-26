import argparse
import random

from game import (
    choose_gift_recipient_interactively,
    choose_room_interactively,
    format_game_result,
    play_game,
)
from player_turn import (
    choose_face_interactively,
    choose_face_to_keep,
    choose_stop_interactively,
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
        help="Choose kept faces, stop checks, tied rooms, and optional gifts.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.seed) if args.seed is not None else random
    choose_face = choose_face_interactively if args.interactive else choose_face_to_keep
    should_stop = choose_stop_interactively if args.interactive else should_stop_automatically
    choose_room = choose_room_interactively if args.interactive else None
    choose_gift_recipient = (
        choose_gift_recipient_interactively if args.interactive else None
    )
    play_kwargs = {}
    if choose_room is not None:
        play_kwargs["choose_room"] = choose_room
    if choose_gift_recipient is not None:
        play_kwargs["choose_gift_recipient"] = choose_gift_recipient
    game_result = play_game(
        args.players,
        rng=rng,
        choose_face=choose_face,
        should_stop=should_stop,
        **play_kwargs,
    )
    if args.interactive:
        print()
    print(format_game_result(game_result))


if __name__ == "__main__":
    main()
