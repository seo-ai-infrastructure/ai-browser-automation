"""The RL feedback orchestrator.

``run_evaluation`` is the entrypoint (invoked by the CLI / a daily cron):

1. Ingest any queued actions into the canonical store.
2. Find actions whose evaluation window has elapsed.
3. For each, gather current outcomes from the configured sources and compute a
   reward (only when at least one source has real data — never fabricated).
4. Persist the reward back onto the action, append a summary to the
   ``rl_rewards`` shared memory block, and (optionally) ask the RL agent to
   reinforce durable knowledge in ``fort_lauderdale_knowledge``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from cloak_seo.client import LettaGateway
from cloak_seo.logging_config import get_logger
from cloak_seo.rl.action_store import ActionStore, get_action_store
from cloak_seo.rl.models import ActionMetrics, RewardBreakdown, TrackedAction
from cloak_seo.rl.reward import compute_reward
from cloak_seo.rl.sources import OutcomeSource, default_sources
from config import Settings, get_settings

logger = get_logger(__name__)

REWARD_BLOCK = "rl_rewards"
KNOWLEDGE_BLOCK = "fort_lauderdale_knowledge"
RL_AGENT = "seo_rl_feedback"


@dataclass
class RewardResult:
    """Outcome of evaluating one action."""

    action: TrackedAction
    current: ActionMetrics
    breakdown: RewardBreakdown
    sources_used: list[str] = field(default_factory=list)

    def summary_line(self) -> str:
        b = self.breakdown
        return (
            f"- [{self.action.created_at.date()}] {self.action.keyword} "
            f"({self.action.target_url}) → reward={b.total:+.3f} "
            f"[rank={b.ranking:+.2f} aio={b.aio:+.2f} "
            f"traffic={b.traffic:+.2f} impr={b.impressions:+.2f}] "
            f"via {', '.join(self.sources_used) or 'no sources'}"
        )


def _gather_current(
    action: TrackedAction, sources: list[OutcomeSource]
) -> tuple[ActionMetrics, list[str]]:
    """Merge current metrics across all available sources."""
    merged = ActionMetrics()
    used: list[str] = []
    for source in sources:
        try:
            result = source.fetch(action)
        except NotImplementedError as exc:
            logger.warning("Source %s present but not implemented: %s", source.name, exc)
            continue
        except Exception as exc:  # noqa: BLE001 - one bad source shouldn't abort
            logger.error("Source %s failed for %s: %s", source.name, action.id, exc)
            continue
        if result.available:
            merged = merged.merged_with(result.metrics)
            used.append(result.source)
    return merged, used


def evaluate_due(
    store: ActionStore,
    sources: list[OutcomeSource],
    settings: Settings,
    now: datetime | None = None,
) -> list[RewardResult]:
    """Evaluate all matured actions that have usable outcome data."""
    now = now or datetime.now(timezone.utc)
    results: list[RewardResult] = []

    for action in store.due(settings.rl_eval_window_days):
        current, used = _gather_current(action, sources)
        if not used:
            logger.info(
                "Action %s is due but no source has data yet — will retry later",
                action.id,
            )
            continue

        breakdown = compute_reward(action.baseline, current, settings)
        action.reward = breakdown.total
        action.evaluated_at = now
        store.save(action)

        results.append(
            RewardResult(action=action, current=current, breakdown=breakdown, sources_used=used)
        )
        logger.info("Evaluated %s: reward=%+.3f", action.id, breakdown.total)

    return results


def _append_to_reward_block(gateway: LettaGateway, results: list[RewardResult]) -> None:
    """Append a dated batch summary to the rl_rewards shared block."""
    block = gateway.find_block(REWARD_BLOCK)
    if block is None:
        logger.warning("Reward block %r missing; run bootstrap first", REWARD_BLOCK)
        return

    stamp = datetime.now(timezone.utc).date()
    section = [f"\n## Evaluation batch {stamp} ({len(results)} actions)"]
    section.extend(r.summary_line() for r in results)
    new_value = (getattr(block, "value", "") or "") + "\n".join(section) + "\n"
    gateway.sdk.blocks.modify(block_id=block.id, value=new_value)
    logger.info("Appended %d reward(s) to %r", len(results), REWARD_BLOCK)


def _reinforce(gateway: LettaGateway, results: list[RewardResult]) -> None:
    """Ask the RL agent to reinforce durable knowledge from the new rewards."""
    agent = gateway.find_agent(RL_AGENT)
    if agent is None:
        logger.warning("RL agent %r not found; skipping reinforcement", RL_AGENT)
        return

    lines = "\n".join(r.summary_line() for r in results)
    prompt = (
        "New 30-day reward signals are in the rl_rewards block:\n\n"
        f"{lines}\n\n"
        f"Update the {KNOWLEDGE_BLOCK} block: strengthen insights tied to "
        "positive rewards and down-weight those tied to negative rewards. Keep "
        "it concise and evidence-based. Do not invent metrics beyond the above."
    )
    try:
        gateway.send_message(agent.id, prompt)
        logger.info("Requested reinforcement from %r", RL_AGENT)
    except Exception as exc:  # noqa: BLE001 - reinforcement is best-effort
        logger.error("Reinforcement message failed: %s", exc)


def run_evaluation(
    gateway: LettaGateway | None = None,
    *,
    reinforce: bool = True,
    now: datetime | None = None,
) -> list[RewardResult]:
    """Full pass: ingest → evaluate due → persist rewards → reinforce."""
    settings = get_settings()
    store = get_action_store()
    sources = default_sources()

    store.ingest_pending()
    results = evaluate_due(store, sources, settings, now=now)

    if not results:
        logger.info("No actions evaluated this run.")
        return results

    gateway = gateway or LettaGateway.connect(settings)
    _append_to_reward_block(gateway, results)
    if reinforce:
        _reinforce(gateway, results)

    return results
