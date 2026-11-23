"""PushProvider port (stub). Notifications only; they never change the pet."""

from __future__ import annotations

from typing import Protocol


class PushProvider(Protocol):
    async def send(self, token: str, title: str, body: str) -> None: ...
