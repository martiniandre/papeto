"""PushProvider port. Notifications only; they never change the pet."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol


class PushOutcome(StrEnum):
    DELIVERED = "delivered"  # accepted by the push service
    INVALID_TOKEN = "invalid_token"  # the device is gone: the caller should forget the token


class PushUnavailableError(Exception):
    """The push service could not be reached or answered with an unexpected error."""


class PushProvider(Protocol):
    async def send(self, token: str, title: str, body: str) -> PushOutcome:
        """Send one notification. Raises `PushUnavailableError` on transport or service errors."""
        ...
