"""Outcome-source interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from cloak_seo.rl.models import ActionMetrics, TrackedAction


@dataclass
class SourceResult:
    """What a source returns for one action."""

    source: str
    available: bool
    metrics: ActionMetrics
    note: str = ""


@runtime_checkable
class OutcomeSource(Protocol):
    """Fetches current outcome metrics for a tracked action."""

    name: str

    def fetch(self, action: TrackedAction) -> SourceResult:
        """Return current metrics for ``action`` (30 days after it was taken)."""
        ...
