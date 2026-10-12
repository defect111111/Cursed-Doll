import argparse
import csv
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import random

try:
    import torch
    from torch.distributions import Categorical
    import torch.nn.functional as F
except ImportError as error:
    raise SystemExit(
        "PyTorch is required for self-play training. Install the CPU build with: "
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
    FACE_TO_ACTION,
    OBSERVED_ROOMS,
    ROOM_TO_ACTION,
)
from ai.model import MaskedActorCritic, mask_logits
from cursed_doll.dice import DEFAULT_DICE_COUNT, FACE_VALUES, TARGET_KEPT_TOTAL, count_dolls, roll_dice
from cursed_doll.game import (
    DOLL_ROOMS,
    create_doll_rooms,
    create_player_dolls,
    fullest_adjustable_rooms,
    move_extra_dolls_for_all_players,
    place_dolls_for_turn,
    room_for_total,
)
from cursed_doll.player_turn import choose_face_to_keep


SELF_PLAY_PHASES = ("choose_face", "stop_check", "choose_room", "gift", "game_over")


class SelfPlayGameEnv:
    """Two-player full-game environment controlled by one shared policy."""

    def __init__(self, rng=None, turn_shaping_coef=0.05, win_reward=1.0):
        self.rng = rng or random.Random()
        self.turn_shaping_coef = turn_shaping_coef
        self.win_reward = win_reward
        self.reset()

    def reset(self):
        self.rooms = create_doll_rooms()
        self.player_dolls = create_player_dolls(2)
        self.current_player = 1
        self.turn_number = 0
        self.winner = None
        self.done = False
        self.phase = "setup"
        self.just_completed_turn_player = None
        self._start_turn_or_finish_game()
        return self.observation()

    @property
    def observation_size(self):
        return len(self.observation())

    def observation(self):
        opponent = self._opponent(self.current_player)
        roll_counts = self._face_counts(self.current_roll)
        kept_counts = self._face_counts(self.kept_dice)
        used_mask = [1.0 if face in self.used_faces else 0.0 for face in FACE_NAMES]
        phase_mask = [1.0 if self.phase == phase else 0.0 for phase in SELF_PLAY_PHASES]
        return [
            self.player_dolls[self.current_player] / 10.0,
            self.player_dolls[opponent] / 10.0,
            *[self.rooms[room] / 10.0 for room in OBSERVED_ROOMS],
            *[count / DEFAULT_DICE_COUNT for count in roll_counts],
            *[count / DEFAULT_DICE_COUNT for count in kept_counts],
            *used_mask,
            self.kept_total / 24.0,
            self.remaining_dice / DEFAULT_DICE_COUNT,
            count_dolls(self.kept_dice) / 12.0,
            *phase_mask,
        ]

    def legal_action_mask(self):
        mask = [False] * ACTION_COUNT
        if self.phase == "choose_face":
            for face in self._available_faces():
                mask[FACE_TO_ACTION[face]] = True
        elif self.phase == "stop_check":
            mask[ACTION_CONTINUE] = True
            mask[ACTION_STOP] = True
        elif self.phase == "choose_room":
            for room in self.tied_rooms:
                mask[ROOM_TO_ACTION[room]] = True
        elif self.phase == "gift":
            mask[ACTION_STOP_GIVING] = True
            if self.gift_remaining > 0 and self.player_dolls[self.current_player] > 0:
                mask[ACTION_GIVE_DOLL] = True
        return mask

    def step(self, action):
        if self.done:
            raise ValueError("Game is already done. Call reset() first.")
        if not self.legal_action_mask()[action]:
            raise ValueError(f"Action {action} is not legal during phase {self.phase}.")

        acting_player = self.current_player
        event = {
            "acting_player": acting_player,
            "turn_completed_player": None,
            "turn_reward": 0.0,
            "terminal_rewards": {},
        }

        if self.phase == "choose_face":
            self._choose_face(ACTION_TO_FACE[action])
        elif self.phase == "stop_check":
            self._choose_stop(action == ACTION_STOP)
        elif self.phase == "choose_room":
            self._apply_placement(ACTION_TO_ROOM[action])
        elif self.phase == "gift":
            if action == ACTION_GIVE_DOLL:
                self._give_doll()
            else:
                self._complete_turn()

        if self.just_completed_turn_player is not None:
            completed_player = self.just_completed_turn_player
            event["turn_completed_player"] = completed_player
            event["turn_reward"] = self.turn_shaping_coef * (
                self.turn_starting_dolls - self.player_dolls[completed_player]
            )
            self.just_completed_turn_player = None

        if self.done:
            loser = self._opponent(self.winner)
            event["terminal_rewards"] = {
                self.winner: self.win_reward,
                loser: -self.win_reward,
            }

        return self.observation(), event, self.done, self.info()

    def info(self):
        return {
            "phase": self.phase,
            "winner": self.winner,
            "current_player": self.current_player,
            "player_dolls": dict(self.player_dolls),
            "rooms": dict(self.rooms),
            "turn_number": self.turn_number,
        }

    def _start_turn_or_finish_game(self):
        if self.player_dolls[self.current_player] == 0:
            self.winner = self.current_player
            self.done = True
            self.phase = "game_over"
            self.current_roll = []
            self.kept_dice = []
            self.used_faces = []
            self.kept_total = 0
            self.remaining_dice = 0
            return

        self.turn_number += 1
        self.remaining_dice = DEFAULT_DICE_COUNT
        self.kept_dice = []
        self.kept_total = 0
        self.used_faces = []
        self.turn_rolls = []
        self.current_roll = []
        self.pending_turn_result = None
        self.pending_placement = None
        self.gift_remaining = 0
        self.gift_recipients = {}
        self.turn_starting_dolls = self.player_dolls[self.current_player]
        self._roll_for_choice()

    def _roll_for_choice(self):
        self.current_roll = roll_dice(self.remaining_dice, self.rng)
        if not self._available_faces():
            self.turn_rolls.append(
                {
                    "roll": list(self.current_roll),
                    "kept_face": None,
                    "kept_dice": [],
                    "kept_total": self.kept_total,
                    "remaining_dice": self.remaining_dice,
                    "can_stop": self.kept_total >= TARGET_KEPT_TOTAL,
                    "stopped": True,
                    "ended_because_no_pattern": True,
                }
            )
            self._finish_turn(stopped=True, ended_because_no_pattern=True)
            return
        self.phase = "choose_face"

    def _choose_face(self, face):
        kept_count = self.current_roll.count(face)
        kept_this_turn = [face] * kept_count
        self.kept_dice.extend(kept_this_turn)
        self.used_faces.append(face)
        self.kept_total += FACE_VALUES[face] * kept_count
        self.remaining_dice -= kept_count
        can_stop = self.kept_total >= TARGET_KEPT_TOTAL
        stopped = can_stop and self.remaining_dice == 0
        self.turn_rolls.append(
            {
                "roll": list(self.current_roll),
                "kept_face": face,
                "kept_dice": kept_this_turn,
                "kept_total": self.kept_total,
                "remaining_dice": self.remaining_dice,
                "can_stop": can_stop,
                "stopped": stopped,
                "ended_because_no_pattern": False,
            }
        )

        if self.remaining_dice == 0:
            self._finish_turn(stopped=stopped, ended_because_no_pattern=False)
        elif can_stop:
            self.phase = "stop_check"
        else:
            self._roll_for_choice()

    def _choose_stop(self, stop):
        if stop:
            self.turn_rolls[-1]["stopped"] = True
            self._finish_turn(stopped=True, ended_because_no_pattern=False)
        else:
            self._roll_for_choice()

    def _finish_turn(self, stopped=False, ended_because_no_pattern=False):
        self.pending_turn_result = {
            "turns": list(self.turn_rolls),
            "kept_dice": list(self.kept_dice),
            "kept_total": self.kept_total,
            "dolls_rolled": count_dolls(self.kept_dice),
            "ignored_dice": (
                self.remaining_dice
                if stopped and not ended_because_no_pattern
                else 0
            ),
            "stopped": stopped,
            "ended_because_no_pattern": ended_because_no_pattern,
        }
        target_room = room_for_total(self.pending_turn_result["kept_total"])
        if target_room is None:
            self.tied_rooms = fullest_adjustable_rooms(self.rooms)
            if len(self.tied_rooms) > 1:
                self.phase = "choose_room"
                return
            target_room = self.tied_rooms[0]
        self._apply_placement(target_room)

    def _apply_placement(self, chosen_room):
        def choose_room(_tied_rooms, **_context):
            return chosen_room

        current_player = self.current_player
        placement = place_dolls_for_turn(
            self.pending_turn_result,
            self.player_dolls[current_player],
            self.rooms,
            apply_overflow=False,
            choose_room=choose_room,
            player_index=current_player,
            player_dolls_by_player=dict(self.player_dolls),
        )
        self.player_dolls[current_player] = placement["dolls_remaining"]
        self.pending_placement = placement
        self.gift_remaining = min(
            self.pending_turn_result["kept_dice"].count("1"),
            self.player_dolls[current_player],
        )
        if placement["dolls_placed"] > 0 and self.gift_remaining > 0:
            self.phase = "gift"
        else:
            self._complete_turn()

    def _give_doll(self):
        current_player = self.current_player
        recipient = self._opponent(current_player)
        self.player_dolls[current_player] -= 1
        self.player_dolls[recipient] += 1
        self.gift_recipients[recipient] = self.gift_recipients.get(recipient, 0) + 1
        self.gift_remaining -= 1
        if self.gift_remaining <= 0 or self.player_dolls[current_player] <= 0:
            self._complete_turn()

    def _complete_turn(self):
        completed_player = self.current_player
        move_extra_dolls_for_all_players(self.player_dolls, self.rooms)
        self.just_completed_turn_player = completed_player
        self.current_player = self._opponent(self.current_player)
        self._start_turn_or_finish_game()

    def _face_counts(self, dice):
        counts = Counter(dice)
        return [counts[face] for face in FACE_NAMES]

    def _available_faces(self):
        used_faces = set(self.used_faces)
        return [face for face in Counter(self.current_roll) if face not in used_faces]

    @staticmethod
    def _opponent(player):
        return 2 if player == 1 else 1


class RandomGameAgent:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def act(self, env):
        legal_actions = [
            action for action, allowed in enumerate(env.legal_action_mask()) if allowed
        ]
        return self.rng.choice(legal_actions)


class LocalTurnGameAgent:
    def act(self, env):
        if env.phase == "choose_face":
            return FACE_TO_ACTION[
                choose_face_to_keep(
                    env.current_roll,
                    kept_total=env.kept_total,
                    used_faces=env.used_faces,
                )
            ]
        if env.phase == "stop_check":
            return ACTION_STOP
        if env.phase == "choose_room":
            return ROOM_TO_ACTION[max(env.tied_rooms, key=lambda room: env.rooms[room])]
        if env.phase == "gift":
            if env.legal_action_mask()[ACTION_GIVE_DOLL]:
                return ACTION_GIVE_DOLL
            return ACTION_STOP_GIVING
        raise ValueError(f"No action for phase {env.phase}.")


class PolicyGameAgent:
    def __init__(self, model, device, greedy=True):
        self.model = model
        self.device = device
        self.greedy = greedy

    def act(self, env):
        observation = torch.tensor([env.observation()], dtype=torch.float32, device=self.device)
        mask = torch.tensor([env.legal_action_mask()], dtype=torch.bool, device=self.device)
        with torch.no_grad():
            logits, _value = self.model(observation)
            masked_logits = mask_logits(logits, mask)
            if self.greedy:
                action = torch.argmax(masked_logits, dim=-1)
            else:
                distribution = Categorical(logits=masked_logits)
                action = distribution.sample()
        return int(action.item())


def parse_args():
    parser = argparse.ArgumentParser(description="Train a two-player self-play policy.")
    parser.add_argument("--updates", type=int, default=40)
    parser.add_argument("--games-per-update", type=int, default=64)
    parser.add_argument("--max-steps-per-game", type=int, default=500)
    parser.add_argument("--ppo-epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--clip-epsilon", type=float, default=0.2)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--turn-shaping-coef", type=float, default=0.05)
    parser.add_argument("--win-reward", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--save-path", default="models/self_play_policy.pt")
    parser.add_argument("--eval-games", type=int, default=100)
    parser.add_argument("--log-dir", default="training_runs")
    parser.add_argument("--run-name", default=None)
    return parser.parse_args()


def collect_self_play_rollouts(model, args, rng, device):
    observations = []
    masks = []
    actions = []
    old_log_probs = []
    rewards = []
    owners = []
    winners = []
    game_lengths = []

    for _game_index in range(args.games_per_update):
        env = SelfPlayGameEnv(
            rng=rng,
            turn_shaping_coef=args.turn_shaping_coef,
            win_reward=args.win_reward,
        )
        active_turn_indices = []
        game_step_indices = []
        done = env.done
        step_count = 0
        while not done and step_count < args.max_steps_per_game:
            owner = env.current_player
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
            step_index = len(rewards)
            observations.append(observation)
            masks.append(mask)
            actions.append(action)
            old_log_probs.append(float(log_prob.item()))
            rewards.append(0.0)
            owners.append(owner)
            active_turn_indices.append(step_index)
            game_step_indices.append(step_index)

            _next_observation, event, done, _info = env.step(action)
            if event["turn_completed_player"] is not None:
                for index in active_turn_indices:
                    rewards[index] += event["turn_reward"]
                active_turn_indices = []

            if done:
                for index in game_step_indices:
                    rewards[index] += event["terminal_rewards"].get(owners[index], 0.0)

            step_count += 1

        if not env.done:
            for index in game_step_indices:
                rewards[index] -= 0.1
        winners.append(env.winner or 0)
        game_lengths.append(step_count)

    returns = torch.tensor(rewards, dtype=torch.float32, device=device)
    return {
        "observations": torch.tensor(observations, dtype=torch.float32, device=device),
        "masks": torch.tensor(masks, dtype=torch.bool, device=device),
        "actions": torch.tensor(actions, dtype=torch.long, device=device),
        "old_log_probs": torch.tensor(old_log_probs, dtype=torch.float32, device=device),
        "returns": returns,
        "average_step_reward": float(returns.mean().item()),
        "average_game_length": sum(game_lengths) / len(game_lengths),
        "player_one_win_rate": winners.count(1) / len(winners),
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


def play_match(agent_by_player, rng, args):
    env = SelfPlayGameEnv(
        rng=rng,
        turn_shaping_coef=args.turn_shaping_coef,
        win_reward=args.win_reward,
    )
    steps = 0
    while not env.done and steps < args.max_steps_per_game:
        action = agent_by_player[env.current_player].act(env)
        _observation, _event, _done, _info = env.step(action)
        steps += 1
    return env.winner or 0, steps


def evaluate_policy(model, device, args, seed_offset=10_000):
    policy = PolicyGameAgent(model, device, greedy=True)
    random_agent = RandomGameAgent(rng=random.Random(args.seed + seed_offset))
    heuristic = LocalTurnGameAgent()
    random_wins = 0
    heuristic_wins = 0
    random_steps = 0
    heuristic_steps = 0
    for game_index in range(args.eval_games):
        winner, steps = play_match(
            {1: policy, 2: random_agent},
            random.Random(args.seed + seed_offset + game_index),
            args,
        )
        random_wins += int(winner == 1)
        random_steps += steps
        winner, steps = play_match(
            {1: policy, 2: heuristic},
            random.Random(args.seed + seed_offset * 2 + game_index),
            args,
        )
        heuristic_wins += int(winner == 1)
        heuristic_steps += steps
    return {
        "vs_random_win_rate": random_wins / args.eval_games,
        "vs_heuristic_win_rate": heuristic_wins / args.eval_games,
        "vs_random_average_steps": random_steps / args.eval_games,
        "vs_heuristic_average_steps": heuristic_steps / args.eval_games,
    }


def create_run_log(args):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = args.run_name or f"self_play_{timestamp}"
    run_dir = Path(args.log_dir) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "config.json").open("w", encoding="utf-8") as config_file:
        json.dump(vars(args), config_file, indent=2, sort_keys=True)
    metrics_path = run_dir / "metrics.csv"
    fieldnames = [
        "update",
        "average_step_reward",
        "average_game_length",
        "self_play_player_one_win_rate",
        "vs_random_win_rate",
        "vs_heuristic_win_rate",
        "best_vs_heuristic_win_rate",
        "saved_best",
    ]
    with metrics_path.open("w", newline="", encoding="utf-8") as metrics_file:
        writer = csv.DictWriter(metrics_file, fieldnames=fieldnames)
        writer.writeheader()
    return {
        "run_dir": run_dir,
        "metrics_path": metrics_path,
        "summary_path": run_dir / "summary.json",
        "fieldnames": fieldnames,
    }


def append_metrics(log, row):
    with log["metrics_path"].open("a", newline="", encoding="utf-8") as metrics_file:
        writer = csv.DictWriter(metrics_file, fieldnames=log["fieldnames"])
        writer.writerow(row)


def main():
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cpu")
    rng = random.Random(args.seed)

    probe_env = SelfPlayGameEnv(rng=random.Random(args.seed))
    model = MaskedActorCritic(probe_env.observation_size, ACTION_COUNT).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    save_dir = os.path.dirname(args.save_path)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    log = create_run_log(args)
    best_score = None
    best_update = None

    print("Training two-player self-play on CPU")
    print(f"Logging run to {log['run_dir']}")
    for update in range(1, args.updates + 1):
        model.train()
        rollout = collect_self_play_rollouts(model, args, rng, device)
        ppo_update(model, optimizer, rollout, args)

        model.eval()
        metrics = evaluate_policy(model, device, args, seed_offset=10_000 + update * 100)
        score = metrics["vs_heuristic_win_rate"]
        saved_best = False
        if best_score is None or score > best_score:
            best_score = score
            best_update = update
            saved_best = True
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "observation_size": probe_env.observation_size,
                    "action_count": ACTION_COUNT,
                    "average_score": score,
                    "args": vars(args),
                },
                args.save_path,
            )

        append_metrics(
            log,
            {
                "update": update,
                "average_step_reward": rollout["average_step_reward"],
                "average_game_length": rollout["average_game_length"],
                "self_play_player_one_win_rate": rollout["player_one_win_rate"],
                "vs_random_win_rate": metrics["vs_random_win_rate"],
                "vs_heuristic_win_rate": metrics["vs_heuristic_win_rate"],
                "best_vs_heuristic_win_rate": best_score,
                "saved_best": int(saved_best),
            },
        )
        print(
            f"update {update:03d} "
            f"step_reward={rollout['average_step_reward']:.3f} "
            f"game_len={rollout['average_game_length']:.1f} "
            f"p1_self={rollout['player_one_win_rate']:.3f} "
            f"vs_random={metrics['vs_random_win_rate']:.3f} "
            f"vs_heuristic={metrics['vs_heuristic_win_rate']:.3f} "
            f"best={best_score:.3f}"
        )

    with log["summary_path"].open("w", encoding="utf-8") as summary_file:
        json.dump(
            {
                "best_update": best_update,
                "best_vs_heuristic_win_rate": best_score,
                "metrics_path": str(log["metrics_path"]),
                "model_path": args.save_path,
                "run_dir": str(log["run_dir"]),
            },
            summary_file,
            indent=2,
            sort_keys=True,
        )
    print(f"Saved best model to {args.save_path}")
    print(f"Saved training log to {log['metrics_path']}")


if __name__ == "__main__":
    main()
