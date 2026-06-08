"""Client adapter for the CloakBrowser Manager service.

CloakBrowser runs as its own container exposing an HTTP API. The browsing
*profile* (geo-targeting to the market, mobile emulation, anti-detect
fingerprint) is configured once in the CloakBrowser Manager dashboard; clients
just reference that profile by id/name.

────────────────────────────────────────────────────────────────────────────
ASSUMED HTTP CONTRACT  (single source of truth — adjust here if it differs)
────────────────────────────────────────────────────────────────────────────
    GET  /health
        → 200 when the service is up.

    POST /sessions/{profile}/navigate   {"url": "...", "wait_until": "load"}
        → {"status": "ok", "final_url": "...", "title": "..."}

    POST /sessions/{profile}/screenshot {"url": "...", "full_page": true}
        → {"status": "ok", "image_base64": "..."}

    POST /sessions/{profile}/extract    {"url": "...", "instructions": "..."}
        → {"status": "ok", "data": {...}}

    POST /sessions/{profile}/action     {"action": "...", "params": {...}}
        → {"status": "ok", "result": {...}}      # generic escape hatch

Authentication (if enabled): ``Authorization: Bearer <CLOAKBROWSER_API_KEY>``.
────────────────────────────────────────────────────────────────────────────

If the real API differs, change the paths/payloads in this one module — nothing
else in the codebase encodes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cloak_seo.logging_config import get_logger
from config import Settings, get_settings

logger = get_logger(__name__)


class CloakBrowserError(RuntimeError):
    """Raised when a CloakBrowser request fails or is misconfigured."""


@dataclass
class CloakBrowserClient:
    """Thin HTTP client for the CloakBrowser Manager service."""

    base_url: str
    profile: str | None
    api_key: str | None
    timeout: float

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "CloakBrowserClient":
        s = settings or get_settings()
        return cls(
            base_url=s.cloakbrowser_url.rstrip("/"),
            profile=s.cloakbrowser_profile,
            api_key=s.cloakbrowser_api_key,
            timeout=s.cloakbrowser_timeout,
        )

    # ── low-level ─────────────────────────────────────────────────────────────
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _profile(self, override: str | None) -> str:
        profile = override or self.profile
        if not profile:
            raise CloakBrowserError(
                "No CloakBrowser profile set. Configure CLOAKBROWSER_PROFILE or pass "
                "profile=... (create it first in the CloakBrowser Manager dashboard)."
            )
        return profile

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        import httpx

        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(
                    method, url, json=payload, headers=self._headers()
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            raise CloakBrowserError(f"CloakBrowser request to {url} failed: {exc}") from exc

    # ── high-level operations ──────────────────────────────────────────────────
    def health(self) -> bool:
        """Return True if the service responds to /health."""
        try:
            self._request("GET", "/health")
            return True
        except CloakBrowserError as exc:
            logger.warning("CloakBrowser health check failed: %s", exc)
            return False

    def navigate(self, url: str, profile: str | None = None, wait_until: str = "load") -> dict:
        p = self._profile(profile)
        return self._request(
            "POST", f"/sessions/{p}/navigate", {"url": url, "wait_until": wait_until}
        )

    def screenshot(self, url: str, profile: str | None = None, full_page: bool = True) -> dict:
        p = self._profile(profile)
        return self._request(
            "POST", f"/sessions/{p}/screenshot", {"url": url, "full_page": full_page}
        )

    def extract(self, url: str, instructions: str, profile: str | None = None) -> dict:
        p = self._profile(profile)
        return self._request(
            "POST", f"/sessions/{p}/extract", {"url": url, "instructions": instructions}
        )

    def action(self, action: str, params: dict[str, Any], profile: str | None = None) -> dict:
        """Generic escape hatch for actions not covered by a typed method."""
        p = self._profile(profile)
        return self._request(
            "POST", f"/sessions/{p}/action", {"action": action, "params": params}
        )
