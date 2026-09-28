import argparse
import random

try:
    import torch
except ImportError as error:
    raise SystemExit(
        "PyTorch is required for the policy demo. Install the CPU build with: "
        "pip install -r requirements-ai.txt"
    ) from error

from ai.env import (
    ACTION_CONTINUE,
    ACTION_COUNT,
    ACTION_GIVE_DOLL,
    ACTION_STOP,
    ACTION_STOP_GIVING,
    ACTION_TO_FACE,
    ACTION_TO_ROOM,
    FACE_NAMES,
    TurnEnv,
)
from ai.model import MaskedActorCritic, mask_logits
from cursed_doll.dice import count_dolls, format_dice
from cursed_doll.game import DOLL_ROOMS


def parse_args():
    parser = argparse.ArgumentParser(description="Demo one model-controlled turn.")
    parser.add_argument("--model-path", default="models/turn_policy.pt")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--greedy",
        action="store_true",
        help="Choose the highest-probability legal action instead of sampling.",
    )
    parser.add_argument("--player-dolls", type=int, default=None)
    parser.add_argument(
        "--rooms",
        default=None,
        help="Optional comma-separated room dolls for rooms 7,8,9,10,11.",
    )
    return parser.parse_args()


def load_policy(model_path):
    device = torch.device("cpu")
    checkpoint = torch.load(model_path, map_location=device)
    model = MaskedActorCritic(
        checkpoint["observation_size"],
        checkpoint.get("action_count", ACTION_COUNT),
    )
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, device


def parse_rooms(raw_rooms):
    if raw_rooms is None:
        return None
    values = [int(value.strip()) for value in raw_rooms.split(",")]
    if len(values) != len(DOLL_ROOMS):
        raise ValueError("Expected five room values for rooms 7,8,9,10,11.")
    return dict(zip(DOLL_ROOMS, values))


def choose_action(model, device, env, greedy=False):
    observation = torch.tensor([env.observation()], dtype=torch.float32, device=device)
    mask = torch.tensor([env.legal_action_mask()], dtype=torch.bool, device=device)
    with torch.no_grad():
        logits, value = model(observation)
        masked_logits = mask_logits(logits, mask)
        probabilities = torch.softmax(masked_logits, dim=-1)[0]
        if greedy:
            action = int(torch.argmax(masked_logits, dim=-1).item())
        else:
            distribution = torch.distributions.Categorical(logits=masked_logits)
            action = int(distribution.sample().item())
    return action, float(value.item()), probabilities.cpu().tolist()


def action_label(action):
    if action in ACTION_TO_FACE:
        return f"keep {ACTION_TO_FACE[action]}"
    if action == ACTION_CONTINUE:
        return "continue rolling"
    if action == ACTION_STOP:
        return "stop turn"
    if action in ACTION_TO_ROOM:
        return f"choose room {ACTION_TO_ROOM[action]}"
    if action == ACTION_GIVE_DOLL:
        return "give one doll"
    if action == ACTION_STOP_GIVING:
        return "stop giving"
    return f"action {action}"


def legal_choice_summary(env, probabilities):
    choices = []
    for action, allowed in enumerate(env.legal_action_mask()):
        if allowed:
            choices.append(f"{action_label(action)} ({probabilities[action]:.2%})")
    return ", ".join(choices)


def print_state(env):
    print(f"Phase       : {env.phase}")
    print(f"Player dolls: {env.player_dolls}")
    print(
        "Rooms       : "
        + ", ".join(f"{room}={env.rooms[room]}" for room in DOLL_ROOMS)
    )
    print(f"Roll        : [{format_dice(env.current_roll)}]")
    print(f"Kept dice   : [{format_dice(env.kept_dice)}]")
    print(f"Kept total  : {env.kept_total}")
    print(f"Kept dolls  : {count_dolls(env.kept_dice)}")
    print(f"Used faces  : [{format_dice(env.used_faces)}]")
    print(f"Remaining   : {env.remaining_dice}")


def main():
    args = parse_args()
    model, device = load_policy(args.model_path)
    rng = random.Random(args.seed)
    env = TurnEnv(rng=rng)

    rooms = parse_rooms(args.rooms)
    if args.player_dolls is not None or rooms is not None:
        env.reset(
            player_dolls=args.player_dolls if args.player_dolls is not None else env.player_dolls,
            rooms=rooms if rooms is not None else env.rooms,
            seed=args.seed,
        )

    print("Cursed Doll policy demo")
    print("=" * 56)
    print(f"Model       : {args.model_path}")
    print(f"Seed        : {args.seed if args.seed is not None else 'random'}")
    print(f"Selection   : {'greedy' if args.greedy else 'sampled'}")
    print(f"Faces       : {', '.join(FACE_NAMES)}")

    step_number = 1
    done = env.done
    reward = 0.0
    info = env.info()
    while not done:
        print("")
        print("-" * 56)
        print(f"Decision {step_number}")
        print_state(env)
        action, value, probabilities = choose_action(
            model,
            device,
            env,
            greedy=args.greedy,
        )
        print(f"Value       : {value:.3f}")
        print(f"Legal       : {legal_choice_summary(env, probabilities)}")
        print(f"Model choice: {action_label(action)}")
        _observation, reward, done, info = env.step(action)
        step_number += 1

    print("")
    print("=" * 56)
    print("Turn result")
    print(f"Start dolls : {info['starting_dolls']}")
    print(f"End dolls   : {info['player_dolls']}")
    print(f"Reward      : {reward:.3f}")
    print(f"Final total : {info['turn_result']['kept_total']}")
    print(f"Final dice  : [{format_dice(info['turn_result']['kept_dice'])}]")
    print(f"Final rooms : {info['rooms']}")
    print(f"Gifted dolls: {info['gifted_dolls']}")
    print(f"Overflow    : {info['overflow_dolls']}")


if __name__ == "__main__":
    main()
