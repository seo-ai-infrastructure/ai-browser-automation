"""Dataclasses for the RL feedback loop, with JSON (de)serialization."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse(dt: str | None) -> datetime | None:
    return datetime.fromisoformat(dt) if dt else None


@dataclass
class ActionMetrics:
    """A snapshot of the metrics that define success for an SEO action.

    ``avg_rank`` uses Google's convention where *lower is better* (1 = top).
    ``None`` means "not measured by the available source".
    """

    avg_rank: float | None = None
    clicks: int = 0
    impressions: int = 0
    aio_cited: bool = False
    aio_citation_count: int = 0

    def merged_with(self, other: "ActionMetrics") -> "ActionMetrics":
        """Overlay ``other``'s measured (non-default) values onto a copy of self."""
        return ActionMetrics(
            avg_rank=other.avg_rank if other.avg_rank is not None else self.avg_rank,
            clicks=other.clicks or self.clicks,
            impressions=other.impressions or self.impressions,
            aio_cited=other.aio_cited or self.aio_cited,
            aio_citation_count=max(other.aio_citation_count, self.aio_citation_count),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ActionMetrics":
        known = {f: data[f] for f in cls.__annotations__ if f in data}
        return cls(**known)


@dataclass
class RewardBreakdown:
    """Per-component contributions to the scalar reward, plus the total."""

    ranking: float = 0.0
    aio: float = 0.0
    traffic: float = 0.0
    impressions: float = 0.0
    total: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrackedAction:
    """An action taken by an agent, tracked for later reward evaluation."""

    target_url: str
    keyword: str
    description: str
    agent: str = "unknown"
    baseline: ActionMetrics = field(default_factory=ActionMetrics)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=_utcnow)
    evaluated_at: datetime | None = None
    reward: float | None = None

    def due_at(self, window_days: int) -> datetime:
        """The earliest time this action may be evaluated."""
        from datetime import timedelta

        return self.created_at + timedelta(days=window_days)

    def is_due(self, window_days: int, now: datetime | None = None) -> bool:
        now = now or _utcnow()
        return self.evaluated_at is None and now >= self.due_at(window_days)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target_url": self.target_url,
            "keyword": self.keyword,
            "description": self.description,
            "agent": self.agent,
            "baseline": self.baseline.to_dict(),
            "created_at": _iso(self.created_at),
            "evaluated_at": _iso(self.evaluated_at),
            "reward": self.reward,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrackedAction":
        return cls(
            id=data.get("id", uuid.uuid4().hex),
            target_url=data["target_url"],
            keyword=data["keyword"],
            description=data.get("description", ""),
            agent=data.get("agent", "unknown"),
            baseline=ActionMetrics.from_dict(data.get("baseline", {})),
            created_at=_parse(data.get("created_at")) or _utcnow(),
            evaluated_at=_parse(data.get("evaluated_at")),
            reward=data.get("reward"),
        )
