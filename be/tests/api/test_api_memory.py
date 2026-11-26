"""API suite against the in-memory UnitOfWork (runs everywhere, no Docker)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from app.api.errors import STATUS_BY_CODE
from app.services.errors import ALL_ERRORS
from tests.api_cases import ApiCases, ConsentRevocationCases
from tests.support.api_env import ApiEnv, build_env
from tests.support.memory import MemoryUowFactory


@pytest.fixture
async def env() -> AsyncIterator[ApiEnv]:
    built = build_env(MemoryUowFactory())
    yield built
    await built.client.aclose()


class TestApiInMemory(ApiCases):
    pass


def test_every_service_error_code_has_an_http_status() -> None:
    codes = {error.code for error in ALL_ERRORS}
    assert codes <= set(STATUS_BY_CODE)


class TestConsentRevocationInMemory(ConsentRevocationCases):
    pass
