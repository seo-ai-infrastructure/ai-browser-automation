"""Reinforcement-learning feedback loop.

The loop closes the gap between *actions* the agents take and the *outcomes*
those actions produce ~30 days later:

    record action  ──(window)──►  fetch outcomes  ──►  compute reward
          │                                                   │
          └────────────── reinforce shared memory ◄───────────┘

Public surface:

* :func:`run_evaluation` — ingest queued actions, evaluate matured ones, write
  rewards into the ``rl_rewards`` shared block, and ask the RL agent to
  reinforce durable knowledge.
* :func:`build_training_dataset` — export reward history as JSONL, the bridge to
  optional MLX QLoRA fine-tuning.
"""

from cloak_seo.rl.feedback import RewardResult, run_evaluation
from cloak_seo.rl.dataset import build_training_dataset
from cloak_seo.rl.models import ActionMetrics, RewardBreakdown, TrackedAction

__all__ = [
    "ActionMetrics",
    "RewardBreakdown",
    "RewardResult",
    "TrackedAction",
    "build_training_dataset",
    "run_evaluation",
]
