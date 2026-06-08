"""Google Search Console outcome source.

Provides clicks, impressions and average position for the action's URL/keyword.
Requires service-account credentials (``GSC_CREDENTIALS_JSON``). When absent,
returns an unavailable result instead of inventing data.
"""

from __future__ import annotations

from cloak_seo.logging_config import get_logger
from cloak_seo.rl.models import ActionMetrics, TrackedAction
from cloak_seo.rl.sources.base import SourceResult
from config import get_settings

logger = get_logger(__name__)


class SearchConsoleSource:
    name = "search_console"

    def fetch(self, action: TrackedAction) -> SourceResult:
        settings = get_settings()
        if not settings.gsc_credentials_json:
            return SourceResult(
                source=self.name,
                available=False,
                metrics=ActionMetrics(),
                note="GSC_CREDENTIALS_JSON not configured.",
            )

        # Live Search Console query lands when credentials are wired up. The
        # contract: query the Search Analytics API for the last N days filtered
        # by page == action.target_url and query == action.keyword, returning
        # clicks, impressions and average position.
        logger.info("GSC fetch for %s / %s", action.target_url, action.keyword)
        raise NotImplementedError(
            "Live Search Console query not yet implemented; credentials present."
        )
