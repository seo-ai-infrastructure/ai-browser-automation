"""Persistence for tracked actions.

Canonical storage is Redis. A pending-queue decouples *recording* (any agent or
the ``record_seo_action`` Letta tool simply RPUSHes a JSON blob) from
*indexing* (this store assigns ids/timestamps and stores the canonical record).

If Redis is unavailable, a process-local in-memory store is used so development
and tests still work — with a clear warning, since data won't persist.
"""

from __future__ import annotations

import json
from typing import Iterable, Protocol

from cloak_seo.logging_config import get_logger
from cloak_seo.rl.models import TrackedAction
from config import get_settings

logger = get_logger(__name__)

# Redis key scheme (source of truth). The Letta tool only needs QUEUE_KEY.
QUEUE_KEY = "cloak:rl:pending_actions"  # RPUSH target for new actions
ACTION_KEY = "cloak:rl:action:{id}"  # per-action JSON
INDEX_KEY = "cloak:rl:actions"  # set of all action ids


class ActionStore(Protocol):
    """Storage interface for tracked actions."""

    def ingest_pending(self) -> list[TrackedAction]: ...
    def save(self, action: TrackedAction) -> None: ...
    def all(self) -> list[TrackedAction]: ...
    def due(self, window_days: int) -> list[TrackedAction]: ...


class RedisActionStore:
    """Redis-backed canonical store."""

    def __init__(self, client) -> None:  # client: redis.Redis
        self._r = client

    def ingest_pending(self) -> list[TrackedAction]:
        """Drain the pending queue into canonical, indexed records."""
        ingested: list[TrackedAction] = []
        while True:
            raw = self._r.lpop(QUEUE_KEY)
            if raw is None:
                break
            try:
                action = TrackedAction.from_dict(json.loads(raw))
            except (ValueError, KeyError) as exc:
                logger.warning("Dropping malformed pending action: %s", exc)
                continue
            self.save(action)
            ingested.append(action)
        if ingested:
            logger.info("Ingested %d pending action(s)", len(ingested))
        return ingested

    def save(self, action: TrackedAction) -> None:
        self._r.set(ACTION_KEY.format(id=action.id), json.dumps(action.to_dict()))
        self._r.sadd(INDEX_KEY, action.id)

    def all(self) -> list[TrackedAction]:
        actions: list[TrackedAction] = []
        for action_id in self._r.smembers(INDEX_KEY):
            raw = self._r.get(ACTION_KEY.format(id=_s(action_id)))
            if raw:
                actions.append(TrackedAction.from_dict(json.loads(raw)))
        return actions

    def due(self, window_days: int) -> list[TrackedAction]:
        return [a for a in self.all() if a.is_due(window_days)]


class InMemoryActionStore:
    """Fallback store used when Redis is unavailable (non-persistent)."""

    def __init__(self) -> None:
        self._queue: list[dict] = []
        self._actions: dict[str, TrackedAction] = {}

    def enqueue(self, payload: dict) -> None:
        self._queue.append(payload)

    def ingest_pending(self) -> list[TrackedAction]:
        ingested = [TrackedAction.from_dict(p) for p in self._queue]
        self._queue.clear()
        for action in ingested:
            self.save(action)
        return ingested

    def save(self, action: TrackedAction) -> None:
        self._actions[action.id] = action

    def all(self) -> list[TrackedAction]:
        return list(self._actions.values())

    def due(self, window_days: int) -> list[TrackedAction]:
        return [a for a in self.all() if a.is_due(window_days)]


def _s(value) -> str:
    """Decode bytes from redis to str if needed."""
    return value.decode() if isinstance(value, (bytes, bytearray)) else str(value)


def get_action_store() -> ActionStore:
    """Return a Redis store if reachable, else an in-memory fallback."""
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        logger.info("Using Redis action store at %s", settings.redis_url)
        return RedisActionStore(client)
    except Exception as exc:  # noqa: BLE001 - any failure -> safe fallback
        logger.warning(
            "Redis unavailable (%s); using in-memory action store (non-persistent)",
            exc,
        )
        return InMemoryActionStore()
