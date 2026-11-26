"""PostHog adapter: plain httpx, key from settings, never raises, no person profiles."""

from __future__ import annotations

import json

import httpx
import pytest

from app.config import Settings
from app.container import ConfigurationError, build_analytics
from app.providers.fake_misc import NoopAnalytics
from app.providers.posthog_analytics import PostHogAnalytics


async def test_posts_event_with_random_id_and_no_person_profile() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"status": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = PostHogAnalytics(api_key="phc_test", host="https://ph.example/", client=client)
    await adapter.track("anon-1", "meal_logged", {"source": "photo"})
    assert str(seen[0].url) == "https://ph.example/capture/"
    body = json.loads(seen[0].content)
    assert body["distinct_id"] == "anon-1"
    assert body["event"] == "meal_logged"
    assert body["properties"] == {"source": "photo", "$process_person_profile": False}


async def test_http_errors_are_swallowed() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    client = httpx.AsyncClient(transport=httpx.MockTransport(boom))
    await PostHogAnalytics(api_key="k", client=client).track("a", "e", {})
    rejected = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    await PostHogAnalytics(api_key="k", client=rejected).track("a", "e", {})


def _settings(**values: object) -> Settings:
    return Settings(jwt_secret="x" * 40, **values)  # type: ignore[arg-type]


def test_disabled_by_default_and_key_required_for_posthog() -> None:
    assert isinstance(build_analytics(_settings()), NoopAnalytics)
    with pytest.raises(ConfigurationError):
        build_analytics(_settings(analytics_provider="posthog"))
    adapter = build_analytics(_settings(analytics_provider="posthog", posthog_api_key="phc_x"))
    assert isinstance(adapter, PostHogAnalytics)
