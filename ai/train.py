import argparse
import os
import random

try:
    import torch
    from torch.distributions import Categorical
    import torch.nn.functional as F
except ImportError as error:
    raise SystemExit(
        "PyTorch is required for training. Install the CPU build with: "
        "pip install torch --index-url https://download.pytorch.org/whl/cpu"
    ) from error

from ai.agents import HeuristicTurnAgent, RandomTurnAgent, evaluate_agent
from ai.env import ACTION_COUNT, TurnEnv
from ai.model import MaskedActorCritic, mask_logits


def parse_args():
    parser = argparse.ArgumentParser(description="Train a CPU PPO turn policy.")
    parser.add_argument("--updates", type=int, default=40)
    parser.add_argument("--episodes-per-update", type=int, default=512)
    parser.add_argument("--ppo-epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--clip-epsilon", type=float, default=0.2)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--save-path", default="models/turn_policy.pt")
    parser.add_argument("--eval-episodes", type=int, default=500)
    return parser.parse_args()


class PolicyAgent:
    def __init__(self, model, device):
        self.model = model
        self.device = device

    def act(self, env):
        observation = torch.tensor([env.observation()], dtype=torch.float32, device=self.device)
        mask = torch.tensor([env.legal_action_mask()], dtype=torch.bool, device=self.device)
        with torch.no_grad():
            logits, _value = self.model(observation)
            action = torch.argmax(mask_logits(logits, mask), dim=-1)
        return int(action.item())


def collect_rollouts(model, episodes, rng, device):
    observations = []
    masks = []
    actions = []
    old_log_probs = []
    returns = []
    rewards = []

    for _episode in range(episodes):
        env = TurnEnv(rng=rng)
        episode_steps = []
        done = env.done
        while not done:
            observation = env.observation()
            mask = env.legal_action_mask()
            observation_tensor = torch.tensor([observation], dtype=torch.float32, device=device)
            mask_tensor = torch.tensor([mask], dtype=torch.bool, device=device)

            with torch.no_grad():
                logits, _value = model(observation_tensor)
                distribution = Categorical(logits=mask_logits(logits, mask_tensor))
                action_tensor = distribution.sample()
                log_prob = distribution.log_prob(action_tensor)

            action = int(action_tensor.item())
            _next_observation, reward, done, _info = env.step(action)
            episode_steps.append((observation, mask, action, float(log_prob.item())))

        for observation, mask, action, log_prob in episode_steps:
            observations.append(observation)
            masks.append(mask)
            actions.append(action)
            old_log_probs.append(log_prob)
            returns.append(env.last_reward)
        rewards.append(env.last_reward)

    return {
        "observations": torch.tensor(observations, dtype=torch.float32, device=device),
        "masks": torch.tensor(masks, dtype=torch.bool, device=device),
        "actions": torch.tensor(actions, dtype=torch.long, device=device),
        "old_log_probs": torch.tensor(old_log_probs, dtype=torch.float32, device=device),
        "returns": torch.tensor(returns, dtype=torch.float32, device=device),
        "average_reward": sum(rewards) / len(rewards),
    }


def ppo_update(model, optimizer, rollout, args):
    observations = rollout["observations"]
    masks = rollout["masks"]
    actions = rollout["actions"]
    old_log_probs = rollout["old_log_probs"]
    returns = rollout["returns"]
    sample_count = observations.shape[0]

    with torch.no_grad():
        _logits, values = model(observations)
        advantages = returns - values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    for _epoch in range(args.ppo_epochs):
        permutation = torch.randperm(sample_count, device=observations.device)
        for start in range(0, sample_count, args.batch_size):
            batch_indices = permutation[start:start + args.batch_size]
            logits, values = model(observations[batch_indices])
            distribution = Categorical(logits=mask_logits(logits, masks[batch_indices]))
            new_log_probs = distribution.log_prob(actions[batch_indices])
            entropy = distribution.entropy().mean()

            ratio = (new_log_probs - old_log_probs[batch_indices]).exp()
            batch_advantages = advantages[batch_indices]
            unclipped = ratio * batch_advantages
            clipped = torch.clamp(
                ratio,
                1.0 - args.clip_epsilon,
                1.0 + args.clip_epsilon,
            ) * batch_advantages
            policy_loss = -torch.min(unclipped, clipped).mean()
            value_loss = F.mse_loss(values, returns[batch_indices])
            loss = policy_loss + args.value_coef * value_loss - args.entropy_coef * entropy

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()


def main():
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cpu")
    rng = random.Random(args.seed)

    probe_env = TurnEnv(rng=random.Random(args.seed))
    model = MaskedActorCritic(probe_env.observation_size, ACTION_COUNT).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)

    save_dir = os.path.dirname(args.save_path)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    best_reward = None
    print("Training on CPU")
    for update in range(1, args.updates + 1):
        model.train()
        rollout = collect_rollouts(model, args.episodes_per_update, rng, device)
        ppo_update(model, optimizer, rollout, args)

        model.eval()
        policy_agent = PolicyAgent(model, device)
        eval_rng = random.Random(args.seed + update)
        random_env_rng = random.Random(args.seed + update + 1000)
        heuristic_env_rng = random.Random(args.seed + update + 2000)
        metrics = evaluate_agent(
            policy_agent,
            lambda: TurnEnv(rng=eval_rng),
            episodes=args.eval_episodes,
        )
        random_metrics = evaluate_agent(
            RandomTurnAgent(rng=random.Random(args.seed + update)),
            lambda: TurnEnv(rng=random_env_rng),
            episodes=args.eval_episodes,
        )
        heuristic_metrics = evaluate_agent(
            HeuristicTurnAgent(),
            lambda: TurnEnv(rng=heuristic_env_rng),
            episodes=args.eval_episodes,
        )
        average_reward = metrics["average_reward"]
        if best_reward is None or average_reward > best_reward:
            best_reward = average_reward
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "observation_size": probe_env.observation_size,
                    "action_count": ACTION_COUNT,
                    "average_reward": average_reward,
                    "args": vars(args),
                },
                args.save_path,
            )

        print(
            f"update {update:03d} "
            f"rollout={rollout['average_reward']:.3f} "
            f"policy={average_reward:.3f} "
            f"random={random_metrics['average_reward']:.3f} "
            f"heuristic={heuristic_metrics['average_reward']:.3f} "
            f"best={best_reward:.3f}"
        )

    print(f"Saved best model to {args.save_path}")


if __name__ == "__main__":
    main()
