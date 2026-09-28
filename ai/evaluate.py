import argparse
import random

try:
    import torch
except ImportError as error:
    raise SystemExit(
        "PyTorch is required to evaluate a saved policy. Install the CPU build with: "
        "pip install torch --index-url https://download.pytorch.org/whl/cpu"
    ) from error

from ai.agents import HeuristicTurnAgent, RandomTurnAgent, evaluate_agent
from ai.env import ACTION_COUNT, TurnEnv
from ai.model import MaskedActorCritic
from ai.train import PolicyAgent


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Cursed Doll turn agents.")
    parser.add_argument("--model-path", default="models/turn_policy.pt")
    parser.add_argument("--episodes", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=11)
    return parser.parse_args()


def main():
    args = parse_args()
    device = torch.device("cpu")
    checkpoint = torch.load(args.model_path, map_location=device)
    model = MaskedActorCritic(
        checkpoint["observation_size"],
        checkpoint.get("action_count", ACTION_COUNT),
    )
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    agents = {
        "policy": PolicyAgent(model, device),
        "random": RandomTurnAgent(rng=random.Random(args.seed)),
        "heuristic": HeuristicTurnAgent(),
    }
    for index, (name, agent) in enumerate(agents.items()):
        env_rng = random.Random(args.seed + index * 1000)
        metrics = evaluate_agent(
            agent,
            lambda: TurnEnv(rng=env_rng),
            episodes=args.episodes,
        )
        print(
            f"{name:9s} "
            f"avg_reward={metrics['average_reward']:.3f} "
            f"avg_terminal_dolls={metrics['average_terminal_dolls']:.3f}"
        )


if __name__ == "__main__":
    main()
