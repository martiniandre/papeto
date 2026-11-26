"""Google sign-in and adult confirmation against the in-memory UnitOfWork."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from tests.google_cases import AdultConfirmationCases, GoogleSignInCases
from tests.support.api_env import ApiEnv, build_env
from tests.support.memory import MemoryUowFactory


@pytest.fixture
async def env() -> AsyncIterator[ApiEnv]:
    built = build_env(MemoryUowFactory())
    yield built
    await built.client.aclose()


class TestGoogleSignInInMemory(GoogleSignInCases):
    pass


class TestAdultConfirmationInMemory(AdultConfirmationCases):
    pass
