"""Turn declarative :class:`AgentDefinition` specs into live Letta agents."""

from __future__ import annotations

from typing import Any

from cloak_seo.agents.definitions import AGENT_DEFINITIONS, AgentDefinition
from cloak_seo.client import LettaGateway
from cloak_seo.logging_config import get_logger

logger = get_logger(__name__)


def _resolve_block_ids(
    definition: AgentDefinition, block_index: dict[str, str]
) -> list[str]:
    """Map a definition's shared-block labels to their ids."""
    ids: list[str] = []
    for label in definition.shared_blocks:
        block_id = block_index.get(label)
        if block_id is None:
            logger.warning(
                "Agent %r references unknown shared block %r — skipping",
                definition.name,
                label,
            )
            continue
        ids.append(block_id)
    return ids


def sync_agents(
    gateway: LettaGateway,
    block_index: dict[str, str],
    tool_index: dict[str, str],
) -> dict[str, Any]:
    """Create-or-update every agent. Returns ``{agent_name: agent}``.

    Args:
        gateway: Connected Letta gateway.
        block_index: ``{block_label: block_id}`` from ``sync_shared_blocks``.
        tool_index: ``{tool_name: tool_id}`` from ``sync_tools``.
    """
    agents: dict[str, Any] = {}

    for definition in AGENT_DEFINITIONS:
        block_ids = _resolve_block_ids(definition, block_index)
        agent = gateway.upsert_agent(
            name=definition.name,
            system=definition.system,
            memory_blocks=definition.memory_blocks(),
            block_ids=block_ids,
            tags=definition.tags,
        )

        # Attach the agent's declared tools (idempotent).
        for tool_name in definition.tools:
            tool_id = tool_index.get(tool_name)
            if tool_id is None:
                logger.warning(
                    "Agent %r references unknown tool %r — skipping",
                    definition.name,
                    tool_name,
                )
                continue
            _attach_tool(gateway, agent.id, tool_id)

        agents[definition.name] = agent

    return agents


def _attach_tool(gateway: LettaGateway, agent_id: str, tool_id: str) -> None:
    """Attach a tool to an agent, ignoring 'already attached' conditions."""
    try:
        gateway.sdk.agents.tools.attach(agent_id=agent_id, tool_id=tool_id)
        logger.info("Attached tool %s to agent %s", tool_id, agent_id)
    except Exception as exc:  # noqa: BLE001 - SDK raises on duplicate attach
        logger.debug("Tool %s attach on %s skipped: %s", tool_id, agent_id, exc)
