"""PostHog adapter with plain httpx (no SDK). Disabled by default (see `build_analytics`).

Posts to the public capture endpoint. The key only comes from settings. It never creates person
profiles and never sends anything but the random analytics id, the event name and coarse
properties. Failures are swallowed and logged without the payload: analytics must never break a
request.
"""

from __future__ import annotations

import httpx
import structlog

log = structlog.get_logger()


class PostHogAnalytics:
    def __init__(
        self,
        *,
        api_key: str,
        host: str = "https://us.i.posthog.com",
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._api_key = api_key
        self._url = host.rstrip("/") + "/capture/"
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)

    async def track(
        self, anonymous_id: str, event: str, properties: dict[str, str | int | bool]
    ) -> None:
        payload = {
            "api_key": self._api_key,
            "event": event,
            "distinct_id": anonymous_id,
            "properties": {**properties, "$process_person_profile": False},
        }
        try:
            response = await self._client.post(self._url, json=payload)
        except httpx.HTTPError:
            log.warning("analytics_unavailable", event_name=event)
            return
        if response.status_code >= 400:
            log.warning("analytics_rejected", event_name=event, status=response.status_code)
