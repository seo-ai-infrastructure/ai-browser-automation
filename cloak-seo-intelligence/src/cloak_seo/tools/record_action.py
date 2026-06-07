"""`record_seo_action` Letta tool.

Lets an agent log an SEO action the moment it is taken, capturing the baseline
metrics that the RL feedback loop will compare against ~30 days later.

Runs on the Letta server, so it is fully self-contained. It only enqueues onto
the Redis pending list (``cloak:rl:pending_actions``) — the Python action store
(``cloak_seo.rl.action_store``) is the source of truth for that key and does the
canonical indexing during evaluation.
"""

from __future__ import annotations


def record_seo_action(
    target_url: str,
    keyword: str,
    description: str,
    baseline_avg_rank: float = -1.0,
    baseline_clicks: int = 0,
    baseline_impressions: int = 0,
    baseline_aio_cited: bool = False,
    agent: str = "unknown",
) -> str:
    """Record an SEO action for later 30-day reward evaluation.

    Args:
        target_url: The page the action targets.
        keyword: The keyword/query the action targets.
        description: What was changed (the agent's proposal/action text).
        baseline_avg_rank: Current average rank (1=top); pass -1 if unknown.
        baseline_clicks: Current clicks over the trailing period.
        baseline_impressions: Current impressions over the trailing period.
        baseline_aio_cited: Whether the page is currently cited in AI Overviews.
        agent: Name of the agent recording the action.

    Returns:
        A short confirmation string.
    """
    import json
    import os

    import redis

    payload = {
        "target_url": target_url,
        "keyword": keyword,
        "description": description,
        "agent": agent,
        "baseline": {
            "avg_rank": None if baseline_avg_rank < 0 else baseline_avg_rank,
            "clicks": baseline_clicks,
            "impressions": baseline_impressions,
            "aio_cited": baseline_aio_cited,
            "aio_citation_count": 1 if baseline_aio_cited else 0,
        },
    }

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis.from_url(redis_url)
    client.rpush("cloak:rl:pending_actions", json.dumps(payload))

    return f"Recorded action for '{keyword}' on {target_url}; queued for RL evaluation."
