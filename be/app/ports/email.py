"""EmailProvider port (stub)."""

from __future__ import annotations

from typing import Protocol


class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...
