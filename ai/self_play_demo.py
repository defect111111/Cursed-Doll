import argparse
import random

try:
    import torch
    from torch.distributions import Categorical
except ImportError as error:
    raise SystemExit(
        "PyTorch is required for the self-play demo. Install the CPU build with: "
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
)
from ai.model import MaskedActorCritic, mask_logits
from ai.self_play import SelfPlayGameEnv
from cursed_doll.dice import count_dolls, format_dice
from cursed_doll.game import DOLL_ROOMS


def parse_args():
    parser = argparse.ArgumentParser(description="Demo one full self-play game.")
    parser.add_argument("--model-path", default="models/self_play_policy.pt")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--greedy",
        action="store_true",
        help="Choose the highest-probability legal action instead of sampling.",
    )
    parser.add_argument("--max-steps", type=int, default=220)
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
            distribution = Categorical(logits=masked_logits)
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
        return "give one doll to opponent"
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
    print(f"Turn        : {env.turn_number}")
    print(f"Phase       : {env.phase}")
    print(f"Player      : {env.current_player}")
    print(
        "Dolls       : "
        + ", ".join(
            f"P{player}={dolls}" for player, dolls in sorted(env.player_dolls.items())
        )
    )
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


def print_event(event):
    if event["turn_completed_player"] is not None:
        print(f"Turn done   : P{event['turn_completed_player']}")
        print(f"Turn reward : {event['turn_reward']:.3f}")
    if event["terminal_rewards"]:
        rewards = ", ".join(
            f"P{player}={reward:.1f}"
            for player, reward in sorted(event["terminal_rewards"].items())
        )
        print(f"Terminal    : {rewards}")


def main():
    args = parse_args()
    model, device = load_policy(args.model_path)
    rng = random.Random(args.seed)
    env = SelfPlayGameEnv(rng=rng)
    if model.backbone[0].in_features != env.observation_size:
        raise SystemExit(
            "This checkpoint does not match the self-play demo observation size. "
            "Use `python -m ai.demo --model-path models/turn_policy.pt` for "
            "single-turn checkpoints."
        )

    print("Cursed Doll self-play policy demo")
    print("=" * 64)
    print(f"Model       : {args.model_path}")
    print(f"Seed        : {args.seed if args.seed is not None else 'random'}")
    print(f"Selection   : {'greedy' if args.greedy else 'sampled'}")
    print(f"Faces       : {', '.join(FACE_NAMES)}")

    step_number = 1
    while not env.done and step_number <= args.max_steps:
        print("")
        print("-" * 64)
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
        _observation, event, _done, _info = env.step(action)
        print_event(event)
        step_number += 1

    print("")
    print("=" * 64)
    if env.done:
        print(f"Winner      : P{env.winner}")
    else:
        print("Winner      : none, max steps reached")
    print(
        "Final dolls : "
        + ", ".join(
            f"P{player}={dolls}" for player, dolls in sorted(env.player_dolls.items())
        )
    )
    print(
        "Final rooms : "
        + ", ".join(f"{room}={env.rooms[room]}" for room in DOLL_ROOMS)
    )


if __name__ == "__main__":
    main()
