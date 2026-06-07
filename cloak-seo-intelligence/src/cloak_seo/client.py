"""Single integration point for the Letta SDK.

Every call into ``letta-client`` is funneled through this module so that:

* the rest of the codebase has a small, stable surface to depend on, and
* if the Letta SDK changes, there is exactly one place to update.

The wrapper is intentionally thin — it exposes the few operations the backend
needs (blocks, agents, messaging) with idempotent, name/label-based lookups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from config import Settings, get_settings

from .logging_config import get_logger

logger = get_logger(__name__)


def _build_sdk_client(settings: Settings) -> Any:
    """Construct the underlying ``letta_client.Letta`` instance.

    Imported lazily so importing this module never requires the SDK to be
    installed (useful for unit tests that monkeypatch the client).
    """
    from letta_client import Letta  # local import keeps import-time deps light

    if settings.is_cloud:
        logger.info("Connecting to Letta Cloud at %s", settings.letta_base_url)
        return Letta(token=settings.letta_api_key, base_url=settings.letta_base_url)

    logger.info("Connecting to self-hosted Letta at %s", settings.letta_base_url)
    return Letta(base_url=settings.letta_base_url)


@dataclass
class LettaGateway:
    """Thin, idempotent facade over the Letta SDK."""

    settings: Settings
    sdk: Any  # letta_client.Letta

    # ── construction ──────────────────────────────────────────────────────────
    @classmethod
    def connect(cls, settings: Settings | None = None) -> "LettaGateway":
        settings = settings or get_settings()
        return cls(settings=settings, sdk=_build_sdk_client(settings))

    # ── shared memory blocks ───────────────────────────────────────────────────
    def find_block(self, label: str) -> Any | None:
        """Return the block with ``label`` if it exists, else ``None``."""
        for block in self.sdk.blocks.list():
            if getattr(block, "label", None) == label:
                return block
        return None

    def upsert_block(self, *, label: str, value: str, description: str) -> Any:
        """Create the block if missing, otherwise update its value/description."""
        existing = self.find_block(label)
        if existing is None:
            logger.info("Creating shared block %r", label)
            return self.sdk.blocks.create(
                label=label, value=value, description=description
            )

        logger.info("Block %r exists (%s) — updating in place", label, existing.id)
        return self.sdk.blocks.modify(
            block_id=existing.id, value=value, description=description
        )

    # ── agents ──────────────────────────────────────────────────────────────────
    def find_agent(self, name: str) -> Any | None:
        """Return the agent named ``name`` if it exists, else ``None``."""
        matches = self.sdk.agents.list(name=name)
        for agent in matches:
            if getattr(agent, "name", None) == name:
                return agent
        return None

    def upsert_agent(
        self,
        *,
        name: str,
        system: str,
        memory_blocks: list[dict[str, str]] | None = None,
        block_ids: Iterable[str] = (),
        tags: Iterable[str] = (),
    ) -> Any:
        """Create or update an agent, returning the agent object.

        ``memory_blocks`` are core-memory blocks owned by this agent (e.g. its
        persona). ``block_ids`` are pre-existing *shared* blocks to attach.
        """
        block_ids = list(block_ids)
        tags = list(tags)
        existing = self.find_agent(name)

        if existing is None:
            logger.info("Creating agent %r", name)
            return self.sdk.agents.create(
                name=name,
                system=system,
                model=self.settings.llm_model,
                embedding=self.settings.embedding_model,
                context_window_limit=self.settings.context_window,
                memory_blocks=memory_blocks or [],
                block_ids=block_ids,
                tags=tags,
            )

        logger.info("Agent %r exists (%s) — syncing config", name, existing.id)
        self.sdk.agents.modify(agent_id=existing.id, system=system, tags=tags)
        self._attach_blocks(existing.id, block_ids)
        return self.find_agent(name)

    def _attach_blocks(self, agent_id: str, block_ids: Iterable[str]) -> None:
        """Attach shared blocks to an agent, skipping any already attached."""
        current = {b.id for b in self.sdk.agents.blocks.list(agent_id=agent_id)}
        for block_id in block_ids:
            if block_id not in current:
                logger.info("Attaching block %s to agent %s", block_id, agent_id)
                self.sdk.agents.blocks.attach(agent_id=agent_id, block_id=block_id)

    def list_agents(self, tags: Iterable[str] = ()) -> list[Any]:
        """List agents, optionally filtered by tags."""
        tags = list(tags)
        if tags:
            return list(self.sdk.agents.list(tags=tags))
        return list(self.sdk.agents.list())

    # ── messaging ──────────────────────────────────────────────────────────────
    def send_message(self, agent_id: str, message: str) -> Any:
        """Send a user message to an agent and return the SDK response."""
        return self.sdk.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": message}],
        )

    @staticmethod
    def extract_reply(response: Any) -> str:
        """Best-effort extraction of assistant text from a messages response.

        Letta returns a typed list of step messages (reasoning, tool calls,
        assistant text, …). We surface assistant/tool-free text content.
        """
        parts: list[str] = []
        for msg in getattr(response, "messages", []) or []:
            # Assistant messages carry the user-visible content.
            if getattr(msg, "message_type", None) == "assistant_message":
                content = getattr(msg, "content", None)
                if isinstance(content, str):
                    parts.append(content)
        return "\n".join(parts).strip()
