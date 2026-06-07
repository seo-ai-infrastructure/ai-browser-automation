"""End-to-end bootstrap: shared memory + tools + agents, wired together.

This is idempotent: running it repeatedly converges the live Letta deployment
to match the declarative definitions in code, without creating duplicates or
clobbering accumulated agent knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cloak_seo.agents.factory import sync_agents
from cloak_seo.client import LettaGateway
from cloak_seo.logging_config import get_logger
from cloak_seo.memory import sync_shared_blocks
from cloak_seo.tools import sync_tools
from config import get_settings

logger = get_logger(__name__)


@dataclass
class BootstrapResult:
    """Outcome of a bootstrap run."""

    blocks: dict[str, str] = field(default_factory=dict)
    tools: dict[str, str] = field(default_factory=dict)
    agents: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"Shared blocks : {', '.join(self.blocks) or '(none)'}",
            f"Tools         : {', '.join(self.tools) or '(none)'}",
            "Agents        :",
        ]
        for name, agent in self.agents.items():
            lines.append(f"  - {name}  ({getattr(agent, 'id', '?')})")
        return "\n".join(lines)


def bootstrap(gateway: LettaGateway | None = None) -> BootstrapResult:
    """Create/sync shared memory, tools and all agents.

    Order matters: blocks and tools must exist before agents can attach them.
    """
    settings = get_settings()
    gateway = gateway or LettaGateway.connect(settings)

    logger.info("Bootstrapping cloak-seo-intelligence for market: %s", settings.market_name)

    blocks = sync_shared_blocks(gateway)
    tools = sync_tools(gateway)
    agents = sync_agents(gateway, block_index=blocks, tool_index=tools)

    result = BootstrapResult(blocks=blocks, tools=tools, agents=agents)
    logger.info("Bootstrap complete.\n%s", result.summary())
    return result
