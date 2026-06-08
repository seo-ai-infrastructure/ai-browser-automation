"""Tests for the CloakBrowser client adapter (mocked HTTP, no live service).

These exercise the *real* ``_request`` method by injecting an httpx
``MockTransport`` via monkeypatching ``httpx.Client`` — so error wrapping,
headers and path construction are all covered for real.
"""

import json

import httpx
import pytest

from cloak_seo.integrations.cloakbrowser import CloakBrowserClient, CloakBrowserError


@pytest.fixture
def make_client(monkeypatch):
    """Return a factory that builds a client wired to a mocked transport."""

    def _factory(handler, profile="ftl-mobile"):
        transport = httpx.MockTransport(handler)
        real_client = httpx.Client

        def _patched(*args, **kwargs):
            kwargs["transport"] = transport
            return real_client(*args, **kwargs)

        monkeypatch.setattr(httpx, "Client", _patched)
        return CloakBrowserClient(
            base_url="http://cloakbrowser:3000",
            profile=profile,
            api_key="secret",
            timeout=5.0,
        )

    return _factory


def test_navigate_hits_profile_path_and_sends_auth(make_client):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("Authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"status": "ok", "final_url": "x", "title": "T"})

    result = make_client(handler).navigate("https://example.com")

    assert result["status"] == "ok"
    assert seen["url"].endswith("/sessions/ftl-mobile/navigate")
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["url"] == "https://example.com"


def test_missing_profile_raises_clear_error(make_client):
    client = make_client(lambda r: httpx.Response(200, json={}), profile=None)
    with pytest.raises(CloakBrowserError, match="profile"):
        client.navigate("https://example.com")


def test_profile_override_takes_precedence(make_client):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"status": "ok", "data": {}})

    make_client(handler).extract("https://example.com", "get the H1", profile="other-profile")

    assert seen["url"].endswith("/sessions/other-profile/extract")


def test_http_error_is_wrapped(make_client):
    client = make_client(lambda r: httpx.Response(500, json={"error": "boom"}))
    with pytest.raises(CloakBrowserError):
        client.navigate("https://example.com")


def test_health_returns_false_when_unreachable(make_client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    assert make_client(handler).health() is False
