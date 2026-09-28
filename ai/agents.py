import random

from ai.env import (
    ACTION_CONTINUE,
    ACTION_GIVE_DOLL,
    ACTION_STOP,
    ACTION_STOP_GIVING,
    FACE_TO_ACTION,
    ROOM_TO_ACTION,
)
from cursed_doll.player_turn import choose_face_to_keep


def legal_actions(mask):
    return [action for action, is_legal in enumerate(mask) if is_legal]


class RandomTurnAgent:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def act(self, env):
        return self.rng.choice(legal_actions(env.legal_action_mask()))


class HeuristicTurnAgent:
    """Greedy baseline for the single-turn reward."""

    def act(self, env):
        if env.phase == "choose_face":
            face = choose_face_to_keep(
                env.current_roll,
                kept_total=env.kept_total,
                used_faces=env.used_faces,
            )
            return FACE_TO_ACTION[face]
        if env.phase == "stop_check":
            return ACTION_STOP
        if env.phase == "choose_room":
            return ROOM_TO_ACTION[max(env.tied_rooms, key=lambda room: env.rooms[room])]
        if env.phase == "gift":
            if env.legal_action_mask()[ACTION_GIVE_DOLL]:
                return ACTION_GIVE_DOLL
            return ACTION_STOP_GIVING
        raise ValueError(f"No action for phase {env.phase}.")


def play_turn(agent, env):
    observation = env.observation()
    done = env.done
    reward = 0.0
    info = env.info()
    while not done:
        action = agent.act(env)
        observation, reward, done, info = env.step(action)
    return reward, info, observation


def evaluate_agent(agent, env_factory, episodes=1000):
    total_reward = 0.0
    terminal_dolls = 0.0
    for _episode in range(episodes):
        env = env_factory()
        reward, info, _observation = play_turn(agent, env)
        total_reward += reward
        terminal_dolls += info["player_dolls"]
    return {
        "episodes": episodes,
        "average_reward": total_reward / episodes,
        "average_terminal_dolls": terminal_dolls / episodes,
    }
