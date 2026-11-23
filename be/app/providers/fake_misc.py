"""No-op or in-memory fakes for the ports that have no real adapter yet."""

from __future__ import annotations


class NoopAnalytics:
    def track(self, anonymous_id: str, event: str, properties: dict[str, str | int | bool]) -> None:
        return None


class NoopErrorReporter:
    def capture(self, error: BaseException) -> None:
        return None


class RecordingPush:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, token: str, title: str, body: str) -> None:
        self.sent.append((token, title, body))


class RecordingEmail:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))
