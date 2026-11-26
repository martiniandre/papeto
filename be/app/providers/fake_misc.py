"""No-op or in-memory fakes for the ports that have no real adapter yet."""

from __future__ import annotations

from app.ports.push import PushOutcome, PushUnavailableError


class NoopAnalytics:
    def track(self, anonymous_id: str, event: str, properties: dict[str, str | int | bool]) -> None:
        return None


class NoopErrorReporter:
    def capture(self, error: BaseException) -> None:
        return None


class RecordingPush:
    """Records deliveries. `invalid_tokens` answer INVALID_TOKEN; `fail` simulates an outage."""

    def __init__(self, *, invalid_tokens: set[str] | None = None, fail: bool = False) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.invalid_tokens = invalid_tokens if invalid_tokens is not None else set()
        self.fail = fail

    async def send(self, token: str, title: str, body: str) -> PushOutcome:
        if self.fail:
            raise PushUnavailableError("fake push outage")
        if token in self.invalid_tokens:
            return PushOutcome.INVALID_TOKEN
        self.sent.append((token, title, body))
        return PushOutcome.DELIVERED


class RecordingEmail:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))
