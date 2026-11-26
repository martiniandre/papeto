"""Push token and notification scenarios against the in-memory UnitOfWork."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from tests.notification_cases import PreferenceCases, PushTokenCases
from tests.support.api_env import ApiEnv, build_env
from tests.support.memory import MemoryUowFactory


@pytest.fixture
async def env() -> AsyncIterator[ApiEnv]:
    built = build_env(MemoryUowFactory())
    yield built
    await built.client.aclose()


class TestPushTokensInMemory(PushTokenCases):
    pass


class TestPreferencesInMemory(PreferenceCases):
    pass
