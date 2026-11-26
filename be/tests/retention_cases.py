"""Account hard delete scenarios (30-day pending period, legal retention), through the worker task.

Shared by the in-memory and Postgres suites; subclasses provide the `env` fixture.
"""

from __future__ import annotations

from datetime import timedelta

from app.providers.fake_misc import RecordingPush
from app.services.retention import LEGAL_RETENTION
from app.worker.tasks import purge_accounts, worker_context
from tests.api_cases import PASSWORD, assert_error, post_meal, signup
from tests.notification_cases import TOKEN
from tests.support.api_env import ApiEnv


async def _purge(env: ApiEnv) -> dict[str, int]:
    push = RecordingPush()
    result = await purge_accounts(worker_context(env.ctx, push))
    assert push.sent == []  # the purge job never sends push notifications
    return result


async def _prepare_full_account(env: ApiEnv, email: str) -> dict[str, str]:
    headers = await signup(env, email)
    assert (await post_meal(env, headers)).status_code == 201
    pushed = await env.client.post(
        "/v1/push-tokens", json={"token": TOKEN, "platform": "ios"}, headers=headers
    )
    assert pushed.status_code == 201
    await env.grant_premium(await env.user_id_for(email))
    return headers


class RetentionCases:
    async def test_nothing_happens_before_the_grace_period_ends(self, env: ApiEnv) -> None:
        headers = await _prepare_full_account(env, "ana@example.com")
        assert (await env.client.delete("/v1/me", headers=headers)).status_code == 202
        env.next_day(29)
        assert await _purge(env) == {"anonymized": 0, "removed": 0}
        assert (await env.client.get("/v1/me", headers=headers)).status_code == 200

    async def test_after_30_days_personal_data_is_erased_and_legal_rows_stay(
        self, env: ApiEnv
    ) -> None:
        headers = await _prepare_full_account(env, "ana@example.com")
        other = await _prepare_full_account(env, "bia@example.com")
        ana_id = await env.user_id_for("ana@example.com")
        assert (await env.client.delete("/v1/me", headers=headers)).status_code == 202
        env.next_day(30)

        assert await _purge(env) == {"anonymized": 1, "removed": 0}

        async with env.ctx.uow_factory() as uow:
            assert await uow.users.get(ana_id) is None
            assert await uow.users.get_by_email("ana@example.com") is None
            assert await uow.meals.list_all(ana_id) == []
            assert await uow.points.list_all(ana_id) == []
            assert await uow.pets.get(ana_id) is None
            assert await uow.push_tokens.list_for_user(ana_id) == []
            assert await uow.usage.logged_days(ana_id) == set()
            assert len(await uow.consents.list_all(ana_id)) == 1  # kept: 5 years
            assert await uow.subscriptions.get(ana_id) is not None  # kept: 5 years

        login = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        assert_error(login, 401, "INVALID_CREDENTIALS")
        assert_error(await env.client.get("/v1/me", headers=headers), 401, "INVALID_TOKEN")

        # Another account is untouched.
        me = await env.client.get("/v1/me", headers=other)
        assert me.status_code == 200
        assert me.json()["email"] == "bia@example.com"
        async with env.ctx.uow_factory() as uow:
            assert await uow.meals.list_all(await env.user_id_for("bia@example.com"))

    async def test_purge_is_idempotent(self, env: ApiEnv) -> None:
        headers = await _prepare_full_account(env, "ana@example.com")
        await env.client.delete("/v1/me", headers=headers)
        env.next_day(31)
        assert (await _purge(env))["anonymized"] == 1
        assert await _purge(env) == {"anonymized": 0, "removed": 0}

    async def test_signing_in_again_cancels_the_deletion(self, env: ApiEnv) -> None:
        headers = await _prepare_full_account(env, "ana@example.com")
        await env.client.delete("/v1/me", headers=headers)
        env.next_day(10)
        back = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        assert back.status_code == 200, back.text
        env.next_day(40)
        assert await _purge(env) == {"anonymized": 0, "removed": 0}

    async def test_user_who_never_asked_to_delete_is_never_touched(self, env: ApiEnv) -> None:
        headers = await _prepare_full_account(env, "ana@example.com")
        env.next_day(100)
        assert await _purge(env) == {"anonymized": 0, "removed": 0}
        assert (await env.client.get("/v1/me", headers=headers)).status_code == 200

    async def test_legal_rows_are_removed_after_the_retention_period(self, env: ApiEnv) -> None:
        headers = await _prepare_full_account(env, "ana@example.com")
        ana_id = await env.user_id_for("ana@example.com")
        await env.client.delete("/v1/me", headers=headers)
        env.next_day(31)
        await _purge(env)
        env.clock.advance(LEGAL_RETENTION - timedelta(days=1))
        assert await _purge(env) == {"anonymized": 0, "removed": 0}
        env.next_day(2)
        assert await _purge(env) == {"anonymized": 0, "removed": 1}
        async with env.ctx.uow_factory() as uow:
            assert await uow.consents.list_all(ana_id) == []
            assert await uow.subscriptions.get(ana_id) is None
