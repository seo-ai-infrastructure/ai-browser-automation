"""Registry that syncs custom tools to the Letta server."""

from __future__ import annotations

from typing import Any, Callable

from cloak_seo.logging_config import get_logger
from cloak_seo.tools.cloakbrowser import cloakbrowser_navigate
from cloak_seo.tools.dataforseo import dataforseo_pull
from cloak_seo.tools.record_action import record_seo_action

logger = get_logger(__name__)

# Map of tool-name -> function. The function name is the tool name in Letta.
TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "dataforseo_pull": dataforseo_pull,
    "record_seo_action": record_seo_action,
    "cloakbrowser_navigate": cloakbrowser_navigate,
}


def sync_tools(gateway: Any) -> dict[str, str]:
    """Register/refresh all custom tools. Returns ``{tool_name: tool_id}``.

    ``create_from_function`` upserts by function name on recent Letta versions;
    we tolerate either an upsert or a create-if-missing semantics.
    """
    name_to_id: dict[str, str] = {}
    for name, func in TOOL_FUNCTIONS.items():
        logger.info("Registering tool %r", name)
        tool = gateway.sdk.tools.upsert_from_function(func=func) if hasattr(
            gateway.sdk.tools, "upsert_from_function"
        ) else gateway.sdk.tools.create_from_function(func=func)
        name_to_id[name] = tool.id
    return name_to_id
