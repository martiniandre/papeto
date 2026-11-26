"""Expo push adapter (https://docs.expo.dev/push-notifications/sending-notifications/).

Only this module talks HTTP to Expo. Never logs tokens, titles or bodies.
"""

from __future__ import annotations

import httpx

from app.ports.push import PushOutcome, PushUnavailableError

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class ExpoPushProvider:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        client: httpx.AsyncClient | None = None,
        url: str = EXPO_PUSH_URL,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._url = url
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)
        self._headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if access_token:
            self._headers["Authorization"] = f"Bearer {access_token}"

    async def send(self, token: str, title: str, body: str) -> PushOutcome:
        payload = {"to": token, "title": title, "body": body, "sound": "default"}
        try:
            response = await self._client.post(self._url, json=payload, headers=self._headers)
        except httpx.HTTPError as exc:
            raise PushUnavailableError("expo push request failed") from exc
        if response.status_code >= 400:
            raise PushUnavailableError(f"expo push answered HTTP {response.status_code}")
        try:
            ticket = response.json()["data"]
            if isinstance(ticket, list):  # a batch answer; we send one message at a time
                ticket = ticket[0]
            status = ticket["status"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise PushUnavailableError("expo push answered an unexpected body") from exc
        if status == "ok":
            return PushOutcome.DELIVERED
        details = ticket.get("details") if isinstance(ticket, dict) else None
        if isinstance(details, dict) and details.get("error") == "DeviceNotRegistered":
            return PushOutcome.INVALID_TOKEN
        raise PushUnavailableError("expo push rejected the message")

    async def aclose(self) -> None:
        await self._client.aclose()
