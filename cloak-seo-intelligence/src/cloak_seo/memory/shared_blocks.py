"""Shared memory blocks for cross-agent coordination.

Letta *shared memory blocks* are pieces of always-in-context memory attached to
multiple agents. An update by any agent is instantly visible to all others —
the backbone of our multi-agent coordination.

We define three shared blocks:

* ``fort_lauderdale_knowledge`` — durable market insights (read by all, written
  by analyzer / optimizer / RL agents).
* ``serp_patterns`` — observed SERP / AI-Overview / Local-Finder patterns from
  the daily pulls.
* ``rl_rewards`` — rolling history of 30-day reward signals for the RL loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from cloak_seo.client import LettaGateway
from cloak_seo.logging_config import get_logger
from config import get_settings

logger = get_logger(__name__)


@dataclass(frozen=True)
class SharedBlock:
    """Definition of a shared memory block."""

    label: str
    description: str
    initial_value: str


def _market() -> str:
    return get_settings().market_name


SHARED_BLOCKS: list[SharedBlock] = [
    SharedBlock(
        label="fort_lauderdale_knowledge",
        description=(
            "Durable, hard-won market knowledge for the target geo. Read by every "
            "agent. Written by the analyzer, optimizer and RL-feedback agents as "
            "insights are validated. Keep it concise and high-signal."
        ),
        initial_value=(
            "# Market knowledge\n"
            "Market: {market}\n\n"
            "## Confirmed insights\n"
            "(none yet — populated as the analyzer validates patterns)\n\n"
            "## Open hypotheses\n"
            "(none yet)\n"
        ),
    ),
    SharedBlock(
        label="serp_patterns",
        description=(
            "Latest observed SERP, AI-Overview and Local-Finder patterns from the "
            "daily pulls (mobile, geo-targeted). Written by researcher/analyzer."
        ),
        initial_value=(
            "# SERP patterns\n"
            "Last updated: never\n\n"
            "## AI Overview wording / citation patterns\n"
            "(none yet)\n\n"
            "## Local Finder / GBP signals\n"
            "(none yet)\n"
        ),
    ),
    SharedBlock(
        label="rl_rewards",
        description=(
            "Rolling history of 30-day reward signals (ranking deltas, AIO "
            "citations gained, traffic). Written by the RL-feedback agent; used to "
            "reinforce useful knowledge in fort_lauderdale_knowledge."
        ),
        initial_value=(
            "# RL reward history\n"
            "(no completed 30-day windows yet)\n"
        ),
    ),
]


def sync_shared_blocks(gateway: LettaGateway) -> dict[str, str]:
    """Create-or-update all shared blocks. Returns ``{label: block_id}``.

    Existing blocks are *not* overwritten with the initial value — we only
    ensure they exist and keep the description current — so accumulated agent
    knowledge is never clobbered on re-bootstrap.
    """
    market = _market()
    label_to_id: dict[str, str] = {}

    for spec in SHARED_BLOCKS:
        existing = gateway.find_block(spec.label)
        if existing is not None:
            # Preserve learned content; refresh description only.
            block = gateway.sdk.blocks.modify(
                block_id=existing.id, description=spec.description
            )
            logger.info("Shared block %r already present", spec.label)
        else:
            block = gateway.upsert_block(
                label=spec.label,
                value=spec.initial_value.format(market=market),
                description=spec.description,
            )
        label_to_id[spec.label] = block.id

    return label_to_id
