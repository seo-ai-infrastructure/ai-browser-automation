"""Tests for the RL reward function and evaluation flow (no external services)."""

from datetime import datetime, timedelta, timezone

import pytest

from cloak_seo.rl.action_store import InMemoryActionStore
from cloak_seo.rl.feedback import evaluate_due
from cloak_seo.rl.models import ActionMetrics, TrackedAction
from cloak_seo.rl.reward import compute_reward
from cloak_seo.rl.sources.base import SourceResult
from config import get_settings


def test_reward_rewards_rank_and_traffic_gains():
    baseline = ActionMetrics(avg_rank=8.0, clicks=100, impressions=1000, aio_cited=False)
    current = ActionMetrics(avg_rank=3.0, clicks=150, impressions=1200, aio_cited=True)

    b = compute_reward(baseline, current)

    assert b.ranking > 0  # moved from 8 -> 3
    assert b.aio == pytest.approx(1.0)  # newly cited
    assert b.traffic > 0
    assert b.total > 0


def test_reward_penalizes_regressions():
    baseline = ActionMetrics(avg_rank=3.0, clicks=200, impressions=2000, aio_cited=True)
    current = ActionMetrics(avg_rank=9.0, clicks=120, impressions=1500, aio_cited=False)

    b = compute_reward(baseline, current)

    assert b.ranking < 0
    assert b.aio == pytest.approx(-1.0)  # lost the citation
    assert b.total < 0


def test_unknown_rank_contributes_zero():
    b = compute_reward(ActionMetrics(avg_rank=None), ActionMetrics(avg_rank=None))
    assert b.ranking == 0.0


class _StubSource:
    """A source that returns fixed current metrics."""

    name = "stub"

    def __init__(self, metrics, available=True):
        self._metrics = metrics
        self._available = available

    def fetch(self, action):
        return SourceResult(
            source=self.name, available=self._available, metrics=self._metrics
        )


def _due_action():
    created = datetime.now(timezone.utc) - timedelta(days=40)
    return TrackedAction(
        target_url="https://example.com/plumber",
        keyword="emergency plumber fort lauderdale",
        description="Added FAQ schema + service-area wording.",
        baseline=ActionMetrics(avg_rank=7.0, clicks=50, impressions=800),
        created_at=created,
    )


def test_evaluate_due_skips_when_no_source_available():
    store = InMemoryActionStore()
    store.save(_due_action())
    sources = [_StubSource(ActionMetrics(), available=False)]

    results = evaluate_due(store, sources, get_settings())

    assert results == []
    assert all(a.evaluated_at is None for a in store.all())  # retried later


def test_evaluate_due_scores_and_marks_evaluated():
    store = InMemoryActionStore()
    store.save(_due_action())
    sources = [_StubSource(ActionMetrics(avg_rank=2.0, clicks=120, impressions=1500))]

    results = evaluate_due(store, sources, get_settings())

    assert len(results) == 1
    result = results[0]
    assert result.breakdown.total > 0
    assert result.sources_used == ["stub"]
    assert store.all()[0].evaluated_at is not None
    assert store.all()[0].reward == result.breakdown.total


def test_not_yet_due_action_is_ignored():
    store = InMemoryActionStore()
    recent = _due_action()
    recent.created_at = datetime.now(timezone.utc) - timedelta(days=2)
    store.save(recent)

    results = evaluate_due(store, [_StubSource(ActionMetrics(avg_rank=1.0))], get_settings())

    assert results == []
