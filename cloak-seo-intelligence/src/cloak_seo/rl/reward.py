"""Reward function: turn a (baseline, current) metric pair into a scalar.

Each component is normalized into roughly [-1, 1] and then combined with the
configured weights. The per-component breakdown is always reported so the RL
agent (and humans) can see *why* a reward was what it was.
"""

from __future__ import annotations

from cloak_seo.rl.models import ActionMetrics, RewardBreakdown
from config import Settings, get_settings


def _ranking_component(baseline: ActionMetrics, current: ActionMetrics) -> float:
    """Positive when average rank improved (rank number went down).

    Normalized by 10 positions and clamped to [-1, 1]. Unknown ranks -> 0.
    """
    if baseline.avg_rank is None or current.avg_rank is None:
        return 0.0
    delta = baseline.avg_rank - current.avg_rank  # >0 means we moved up
    return max(-1.0, min(1.0, delta / 10.0))


def _aio_component(baseline: ActionMetrics, current: ActionMetrics) -> float:
    """Reward gaining AI-Overview citations; penalize losing them."""
    if current.aio_cited and not baseline.aio_cited:
        return 1.0
    if baseline.aio_cited and not current.aio_cited:
        return -1.0
    delta = current.aio_citation_count - baseline.aio_citation_count
    return max(-1.0, min(1.0, delta / 3.0))


def _ratio_delta(before: int, after: int) -> float:
    """Relative change, clamped to [-1, 1]. Treats 0->positive as full credit."""
    if before <= 0:
        return 1.0 if after > 0 else 0.0
    return max(-1.0, min(1.0, (after - before) / before))


def compute_reward(
    baseline: ActionMetrics,
    current: ActionMetrics,
    settings: Settings | None = None,
) -> RewardBreakdown:
    """Compute the weighted reward and its component breakdown."""
    settings = settings or get_settings()

    ranking = _ranking_component(baseline, current)
    aio = _aio_component(baseline, current)
    traffic = _ratio_delta(baseline.clicks, current.clicks)
    impressions = _ratio_delta(baseline.impressions, current.impressions)

    total = (
        settings.rl_weight_ranking * ranking
        + settings.rl_weight_aio * aio
        + settings.rl_weight_traffic * traffic
        + settings.rl_weight_impressions * impressions
    )

    return RewardBreakdown(
        ranking=round(ranking, 4),
        aio=round(aio, 4),
        traffic=round(traffic, 4),
        impressions=round(impressions, 4),
        total=round(total, 4),
    )
