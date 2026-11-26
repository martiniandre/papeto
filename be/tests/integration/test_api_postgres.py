"""The shared API scenarios against real Postgres (unverified where Docker is unavailable)."""

from __future__ import annotations

import asyncio

import pytest

from tests.api_cases import ApiCases, ConsentRevocationCases, allocate, signup
from tests.support.api_env import ApiEnv

pytestmark = pytest.mark.integration


class TestApiPostgres(ApiCases):
    async def test_parallel_attribute_spends_cannot_overspend(self, env: ApiEnv) -> None:
        headers = await signup(env)  # level 1: exactly one point to spend
        responses = await asyncio.gather(
            *(allocate(env, headers, {"allocations": {name: 1}}) for name in ("speed", "skill"))
        )
        assert sorted(r.status_code for r in responses) == [200, 400]
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert sum(pet["attributes"].values()) == 1
        assert pet["unspent_attribute_points"] == 0


class TestConsentRevocationPostgres(ConsentRevocationCases):
    pass
