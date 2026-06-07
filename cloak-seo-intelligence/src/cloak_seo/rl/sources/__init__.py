"""Outcome data sources for the RL feedback loop.

Each source fetches *current* metrics for a tracked action. They share the
:class:`OutcomeSource` interface so new providers drop in cleanly. Real API
calls require credentials; without them, sources report ``available = False``
and contribute nothing (rather than fabricating numbers).
"""

from cloak_seo.rl.sources.analytics import AnalyticsSource
from cloak_seo.rl.sources.base import OutcomeSource, SourceResult
from cloak_seo.rl.sources.bing import BingSource
from cloak_seo.rl.sources.search_console import SearchConsoleSource


def default_sources() -> list[OutcomeSource]:
    """Construct the standard set of outcome sources from settings."""
    return [SearchConsoleSource(), AnalyticsSource(), BingSource()]


__all__ = [
    "AnalyticsSource",
    "BingSource",
    "OutcomeSource",
    "SearchConsoleSource",
    "SourceResult",
    "default_sources",
]
