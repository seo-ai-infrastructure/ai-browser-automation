"""`cloakbrowser_navigate` Letta tool.

Lets the executor agent drive the CloakBrowser Manager service to visit a page
(using the geo/mobile/anti-detect profile configured in the dashboard) and
optionally extract information.

Runs on the Letta server, so it is fully self-contained and uses only the
standard library. The HTTP contract mirrors
``cloak_seo.integrations.cloakbrowser`` (the source of truth for the API shape).
"""

from __future__ import annotations


def cloakbrowser_navigate(url: str, extract_instructions: str = "") -> str:
    """Visit a URL through CloakBrowser and optionally extract information.

    Args:
        url: The page to visit.
        extract_instructions: If non-empty, what to extract from the page
            (natural-language instructions handled by CloakBrowser).

    Returns:
        A JSON string with the result, or a clearly-labelled status payload when
        CloakBrowser is unconfigured or unreachable (never fabricated content).
    """
    import json
    import os
    import urllib.error
    import urllib.request

    base_url = os.getenv("CLOAKBROWSER_URL", "http://cloakbrowser:3000").rstrip("/")
    profile = os.getenv("CLOAKBROWSER_PROFILE")
    api_key = os.getenv("CLOAKBROWSER_API_KEY")
    timeout = float(os.getenv("CLOAKBROWSER_TIMEOUT", "60"))

    if not profile:
        return json.dumps(
            {
                "status": "not_configured",
                "reason": "CLOAKBROWSER_PROFILE is not set.",
                "hint": "Create a profile in the CloakBrowser Manager dashboard and "
                "set CLOAKBROWSER_PROFILE.",
            }
        )

    if extract_instructions:
        path = f"/sessions/{profile}/extract"
        payload = {"url": url, "instructions": extract_instructions}
    else:
        path = f"/sessions/{profile}/navigate"
        payload = {"url": url, "wait_until": "load"}

    request = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        return json.dumps(
            {
                "status": "unreachable",
                "reason": f"CloakBrowser request failed: {exc}",
                "target": f"{base_url}{path}",
            }
        )
