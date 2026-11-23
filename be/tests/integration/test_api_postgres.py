"""The shared API scenarios against real Postgres (unverified where Docker is unavailable)."""

from __future__ import annotations

import pytest

from tests.api_cases import ApiCases

pytestmark = pytest.mark.integration


class TestApiPostgres(ApiCases):
    pass
