import torch
from torch import nn


class MaskedActorCritic(nn.Module):
    def __init__(self, observation_size, action_count, hidden_size=64):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(observation_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
        )
        self.actor = nn.Linear(hidden_size, action_count)
        self.critic = nn.Linear(hidden_size, 1)

    def forward(self, observations):
        features = self.backbone(observations)
        return self.actor(features), self.critic(features).squeeze(-1)


def mask_logits(logits, masks):
    return logits.masked_fill(~masks.bool(), -1.0e9)
