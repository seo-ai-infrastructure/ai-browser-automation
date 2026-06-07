"""Export evaluated actions as a fine-tuning dataset.

This is the bridge from the RL loop to *optional* MLX QLoRA domain adaptation:
each evaluated action becomes an instruction/response example, weighted by its
reward, so positive-reward decisions are reinforced during fine-tuning. The
actual MLX QLoRA training script is a separate, later milestone — this produces
the JSONL it will consume.
"""

from __future__ import annotations

import json
from pathlib import Path

from cloak_seo.logging_config import get_logger
from cloak_seo.rl.action_store import get_action_store
from cloak_seo.rl.models import TrackedAction

logger = get_logger(__name__)


def _example(action: TrackedAction) -> dict:
    """Render one evaluated action as a chat-style training example."""
    outcome = "succeeded" if (action.reward or 0) > 0 else "underperformed"
    return {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Target keyword: {action.keyword}\n"
                    f"Page: {action.target_url}\n"
                    "Propose an SEO optimization for this local-market target."
                ),
            },
            {"role": "assistant", "content": action.description},
        ],
        # Reward used as a sample weight by the trainer (later milestone).
        "reward": action.reward,
        "label": outcome,
    }


def build_training_dataset(
    output_path: str | Path,
    *,
    min_reward: float | None = None,
) -> int:
    """Write evaluated actions to ``output_path`` as JSONL. Returns the count.

    Args:
        output_path: Destination ``.jsonl`` file.
        min_reward: If set, only include actions whose reward >= this threshold
            (e.g. ``0.0`` to keep only net-positive examples).
    """
    store = get_action_store()
    evaluated = [a for a in store.all() if a.evaluated_at is not None]
    if min_reward is not None:
        evaluated = [a for a in evaluated if (a.reward or 0) >= min_reward]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for action in evaluated:
            fh.write(json.dumps(_example(action)) + "\n")

    logger.info("Wrote %d training example(s) to %s", len(evaluated), output_path)
    return len(evaluated)
