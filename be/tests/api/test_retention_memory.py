"""Account hard delete scenarios against the in-memory UnitOfWork."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from tests.retention_cases import RetentionCases
from tests.support.api_env import ApiEnv, build_env
from tests.support.memory import MemoryUowFactory


@pytest.fixture
async def env() -> AsyncIterator[ApiEnv]:
    built = build_env(MemoryUowFactory())
    yield built
    await built.client.aclose()


class TestRetentionInMemory(RetentionCases):
    pass
