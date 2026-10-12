import argparse
from dataclasses import dataclass
import random

try:
    import torch
except ImportError as error:
    raise SystemExit(
        "PyTorch is required for self-play evaluation. Install the CPU build with: "
        "pip install -r requirements-ai.txt"
    ) from error

from ai.env import ACTION_COUNT
from ai.model import MaskedActorCritic
from ai.self_play import (
    LocalTurnGameAgent,
    PolicyGameAgent,
    RandomGameAgent,
    SelfPlayGameEnv,
)


@dataclass
class MatchConfig:
    max_steps_per_game: int
    turn_shaping_coef: float
    win_reward: float


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a full-game self-play policy.")
    parser.add_argument("--model-path", default="models/self_play_policy.pt")
    parser.add_argument("--games", type=int, default=500)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--max-steps-per-game", type=int, default=500)
    parser.add_argument("--turn-shaping-coef", type=float, default=0.05)
    parser.add_argument("--win-reward", type=float, default=1.0)
    parser.add_argument(
        "--sampled",
        action="store_true",
        help="Sample policy actions instead of using greedy actions.",
    )
    return parser.parse_args()


def load_policy(model_path, greedy=True):
    device = torch.device("cpu")
    checkpoint = torch.load(model_path, map_location=device)
    model = MaskedActorCritic(
        checkpoint["observation_size"],
        checkpoint.get("action_count", ACTION_COUNT),
    )
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    probe_env = SelfPlayGameEnv(rng=random.Random(0))
    if model.backbone[0].in_features != probe_env.observation_size:
        raise SystemExit(
            "This checkpoint does not match the self-play evaluator observation size. "
            "Use `python -m ai.evaluate --model-path models/turn_policy.pt` for "
            "single-turn checkpoints."
        )
    return PolicyGameAgent(model, device, greedy=greedy)


def play_match(agent_by_player, rng, config):
    env = SelfPlayGameEnv(
        rng=rng,
        turn_shaping_coef=config.turn_shaping_coef,
        win_reward=config.win_reward,
    )
    steps = 0
    while not env.done and steps < config.max_steps_per_game:
        action = agent_by_player[env.current_player].act(env)
        _observation, _event, _done, _info = env.step(action)
        steps += 1
    return env.winner or 0, steps


def evaluate_seated(policy, opponent_factory, args, policy_player):
    config = MatchConfig(
        max_steps_per_game=args.max_steps_per_game,
        turn_shaping_coef=args.turn_shaping_coef,
        win_reward=args.win_reward,
    )
    policy_wins = 0
    timeouts = 0
    total_steps = 0
    for game_index in range(args.games):
        opponent = opponent_factory(game_index)
        agents = {
            policy_player: policy,
            2 if policy_player == 1 else 1: opponent,
        }
        winner, steps = play_match(
            agents,
            random.Random(args.seed + policy_player * 100_000 + game_index),
            config,
        )
        policy_wins += int(winner == policy_player)
        timeouts += int(winner == 0)
        total_steps += steps
    return {
        "policy_win_rate": policy_wins / args.games,
        "average_steps": total_steps / args.games,
        "timeouts": timeouts,
    }


def evaluate_policy_vs_policy(policy, args):
    config = MatchConfig(
        max_steps_per_game=args.max_steps_per_game,
        turn_shaping_coef=args.turn_shaping_coef,
        win_reward=args.win_reward,
    )
    player_one_wins = 0
    timeouts = 0
    total_steps = 0
    for game_index in range(args.games):
        winner, steps = play_match(
            {1: policy, 2: policy},
            random.Random(args.seed + 300_000 + game_index),
            config,
        )
        player_one_wins += int(winner == 1)
        timeouts += int(winner == 0)
        total_steps += steps
    return {
        "player_one_win_rate": player_one_wins / args.games,
        "average_steps": total_steps / args.games,
        "timeouts": timeouts,
    }


def print_seated_metrics(label, p1_metrics, p2_metrics):
    combined_win_rate = (
        p1_metrics["policy_win_rate"] + p2_metrics["policy_win_rate"]
    ) / 2
    combined_steps = (p1_metrics["average_steps"] + p2_metrics["average_steps"]) / 2
    print(
        f"{label:12s} "
        f"policy_win={combined_win_rate:.3f} "
        f"as_p1={p1_metrics['policy_win_rate']:.3f} "
        f"as_p2={p2_metrics['policy_win_rate']:.3f} "
        f"avg_steps={combined_steps:.1f} "
        f"timeouts={p1_metrics['timeouts'] + p2_metrics['timeouts']}"
    )


def main():
    args = parse_args()
    policy = load_policy(args.model_path, greedy=not args.sampled)

    print("Cursed Doll self-play evaluation")
    print("=" * 72)
    print(f"Model       : {args.model_path}")
    print(f"Games/seat  : {args.games}")
    print(f"Selection   : {'sampled' if args.sampled else 'greedy'}")
    print(f"Seed        : {args.seed}")
    print("")

    random_p1 = evaluate_seated(
        policy,
        lambda game_index: RandomGameAgent(rng=random.Random(args.seed + game_index)),
        args,
        policy_player=1,
    )
    random_p2 = evaluate_seated(
        policy,
        lambda game_index: RandomGameAgent(rng=random.Random(args.seed + 10_000 + game_index)),
        args,
        policy_player=2,
    )
    print_seated_metrics("vs_random", random_p1, random_p2)

    heuristic_p1 = evaluate_seated(
        policy,
        lambda _game_index: LocalTurnGameAgent(),
        args,
        policy_player=1,
    )
    heuristic_p2 = evaluate_seated(
        policy,
        lambda _game_index: LocalTurnGameAgent(),
        args,
        policy_player=2,
    )
    print_seated_metrics("vs_heuristic", heuristic_p1, heuristic_p2)

    self_metrics = evaluate_policy_vs_policy(policy, args)
    print(
        f"{'self_play':12s} "
        f"p1_win={self_metrics['player_one_win_rate']:.3f} "
        f"avg_steps={self_metrics['average_steps']:.1f} "
        f"timeouts={self_metrics['timeouts']}"
    )


if __name__ == "__main__":
    main()
