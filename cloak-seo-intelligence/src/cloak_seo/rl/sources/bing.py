"""Bing Webmaster Tools outcome source (supplementary).

Contributes Bing clicks/impressions and rank. Requires ``BING_WEBMASTER_API_KEY``.
"""

from __future__ import annotations

from cloak_seo.logging_config import get_logger
from cloak_seo.rl.models import ActionMetrics, TrackedAction
from cloak_seo.rl.sources.base import SourceResult
from config import get_settings

logger = get_logger(__name__)


class BingSource:
    name = "bing"

    def fetch(self, action: TrackedAction) -> SourceResult:
        settings = get_settings()
        if not settings.bing_api_key:
            return SourceResult(
                source=self.name,
                available=False,
                metrics=ActionMetrics(),
                note="BING_WEBMASTER_API_KEY not configured.",
            )

        logger.info("Bing fetch for %s / %s", action.target_url, action.keyword)
        raise NotImplementedError(
            "Live Bing Webmaster query not yet implemented; api key present."
        )
