"""DataForSEO pull tool.

This function is registered as a Letta tool and executed *on the Letta server*.
For that reason it must be fully self-contained: all imports happen inside the
body and configuration is read from the server's environment.

This milestone ships the tool *interface* with a safe, clearly-labelled stub
return when credentials are absent. The full DataForSEO + CloakBrowser pipeline
lands in the next milestone; the agents and orchestration are already wired to
call this, so only the body changes.
"""

from __future__ import annotations


def dataforseo_pull(keyword: str, search_type: str = "organic") -> str:
    """Pull geo-targeted, mobile SERP data for the target market.

    Args:
        keyword: The search query to pull (e.g. "emergency plumber").
        search_type: One of "organic", "ai_overview", or "local_finder".

    Returns:
        A JSON string with the pulled results, or a clearly-labelled stub
        payload when DataForSEO credentials are not configured.
    """
    import json
    import os

    login = os.getenv("DATAFORSEO_LOGIN")
    password = os.getenv("DATAFORSEO_PASSWORD")
    location_code = os.getenv("CLOAK_MARKET_LOCATION_CODE", "1015214")
    language = os.getenv("CLOAK_MARKET_LANGUAGE", "en")

    if not (login and password):
        return json.dumps(
            {
                "status": "stub",
                "reason": "DATAFORSEO credentials not configured",
                "request": {
                    "keyword": keyword,
                    "search_type": search_type,
                    "location_code": location_code,
                    "language": language,
                    "device": "mobile",
                },
                "note": "Configure DATAFORSEO_LOGIN/PASSWORD to enable live pulls.",
            }
        )

    # NOTE: live DataForSEO call lands in the data-pipeline milestone. The
    # request shape above is the contract the live implementation will fulfil.
    return json.dumps(
        {
            "status": "not_implemented",
            "reason": "Live DataForSEO pull arrives in the data-pipeline milestone.",
            "request": {"keyword": keyword, "search_type": search_type},
        }
    )
