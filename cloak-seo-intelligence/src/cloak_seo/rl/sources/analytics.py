"""Google Analytics 4 outcome source.

Contributes traffic signals (treated as ``clicks`` for reward purposes) for the
action's landing page. Requires ``GA4_PROPERTY_ID`` (and ADC credentials).
"""

from __future__ import annotations

from cloak_seo.logging_config import get_logger
from cloak_seo.rl.models import ActionMetrics, TrackedAction
from cloak_seo.rl.sources.base import SourceResult
from config import get_settings

logger = get_logger(__name__)


class AnalyticsSource:
    name = "analytics"

    def fetch(self, action: TrackedAction) -> SourceResult:
        settings = get_settings()
        if not settings.ga4_property_id:
            return SourceResult(
                source=self.name,
                available=False,
                metrics=ActionMetrics(),
                note="GA4_PROPERTY_ID not configured.",
            )

        # Live GA4 Data API query lands when configured. Contract: organic
        # sessions for landingPage == action.target_url over the window.
        logger.info("GA4 fetch for %s", action.target_url)
        raise NotImplementedError(
            "Live GA4 query not yet implemented; property id present."
        )
