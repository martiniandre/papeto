"""Notice scenarios (RF-40 to RF-42) through the real services and worker task functions.

Shared by the in-memory and Postgres suites; subclasses provide the `env` fixture. The ARQ task
functions are called directly (no Redis). `START` is 09:00 in Sao Paulo, outside quiet hours.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain import MAX_NOTICES_PER_DAY, NOTICE_COPY, NoticeKind
from app.ports.repositories import NoticeRecord
from app.providers.fake_misc import RecordingPush
from app.worker.tasks import send_notices, worker_context
from tests.api_cases import post_meal, signup
from tests.notification_cases import OTHER_TOKEN, TOKEN
from tests.support.api_env import ApiEnv

ALL_COPY = {(c.title, c.body): kind for kind, options in NOTICE_COPY.items() for c in options}


async def _register_token(env: ApiEnv, headers: dict[str, str], token: str = TOKEN) -> None:
    response = await env.client.post(
        "/v1/push-tokens", json={"token": token, "platform": "ios"}, headers=headers
    )
    assert response.status_code == 201


async def _run(env: ApiEnv, push: RecordingPush) -> dict[str, int]:
    return await send_notices(worker_context(env.ctx, push))


def _kinds(push: RecordingPush) -> list[NoticeKind]:
    return [ALL_COPY[(title, body)] for _, title, body in push.sent]


class NoticeCases:
    @pytest.fixture
    def push(self) -> RecordingPush:
        return RecordingPush()

    async def test_tired_pet_gets_one_notice_and_never_a_second(
        self, env: ApiEnv, push: RecordingPush
    ) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        result = await _run(env, push)
        assert result == {"users_checked": 1, "notices_sent": 1, "failures": 0}
        assert _kinds(push) == [NoticeKind.TIRED]
        assert push.sent[0][0] == TOKEN
        await _run(env, push)
        env.clock.advance(timedelta(hours=2))
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED]

    async def test_sleepy_notice_follows_in_the_same_episode_then_silence_after_fainting(
        self, env: ApiEnv, push: RecordingPush
    ) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        await _run(env, push)  # day 1: tired
        env.next_day()
        await _run(env, push)  # day 2: one life lost -> sleepy
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED, NoticeKind.SLEEPY]
        env.next_day()
        await _run(env, push)  # day 3: fainted -> nothing
        env.next_day(5)
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED, NoticeKind.SLEEPY]

    async def test_worker_never_changes_the_pet(self, env: ApiEnv, push: RecordingPush) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        user_id = await env.user_id_for("ana@example.com")
        async with env.ctx.uow_factory() as uow:
            before = await uow.pets.get(user_id)
        env.next_day(3)  # three missed days: fainted in the read model
        await _run(env, push)
        async with env.ctx.uow_factory() as uow:
            after = await uow.pets.get(user_id)
        assert before == after
        assert after is not None
        assert after.state.lives == 2

    async def test_quiet_hours_block_then_release_in_local_time(
        self, env: ApiEnv, push: RecordingPush
    ) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        env.clock.set(datetime(2026, 3, 10, 1, 30, tzinfo=UTC))  # 22:30 on Mar 9, Sao Paulo
        await _run(env, push)
        assert push.sent == []
        env.clock.set(datetime(2026, 3, 10, 10, 59, tzinfo=UTC))  # 07:59 local
        await _run(env, push)
        assert push.sent == []
        env.clock.set(datetime(2026, 3, 10, 11, 0, tzinfo=UTC))  # 08:00 local
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED]

    async def test_quiet_hours_use_the_users_timezone_with_dst(
        self, env: ApiEnv, push: RecordingPush
    ) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        patched = await env.client.patch(
            "/v1/me", json={"timezone": "America/New_York"}, headers=headers
        )
        assert patched.status_code == 200
        env.clock.set(datetime(2026, 3, 10, 11, 59, tzinfo=UTC))  # 07:59 EDT (DST began Mar 8)
        await _run(env, push)
        assert push.sent == []
        env.clock.set(datetime(2026, 3, 10, 12, 0, tzinfo=UTC))  # 08:00 EDT
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED]

    async def test_custom_quiet_hours_are_respected(self, env: ApiEnv, push: RecordingPush) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        await env.client.patch(
            "/v1/me",
            json={"notifications": {"quiet_hours_start": "08:00", "quiet_hours_end": "10:00"}},
            headers=headers,
        )
        await _run(env, push)  # 09:00 local, inside the custom window
        assert push.sent == []
        env.clock.advance(timedelta(hours=1))
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED]

    async def test_switches_turn_notices_off(self, env: ApiEnv, push: RecordingPush) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        await env.client.patch(
            "/v1/me",
            json={"notifications": {"meal_reminder": False, "sleepy_notice": False}},
            headers=headers,
        )
        await _run(env, push)
        env.next_day()
        await _run(env, push)
        assert push.sent == []

    async def test_daily_cap_blocks_a_third_notice(self, env: ApiEnv, push: RecordingPush) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        user_id = await env.user_id_for("ana@example.com")
        async with env.ctx.uow_factory() as uow:
            for index in range(MAX_NOTICES_PER_DAY):
                added = await uow.notices.add_if_new(
                    NoticeRecord(
                        id=env.ctx.ids.new_id(),
                        user_id=user_id,
                        kind=NoticeKind.TIRED,
                        episode_day=date(2026, 1, 1 + index),
                        local_day=date(2026, 3, 10),
                        sent_at=env.clock.now(),
                    )
                )
                assert added
            await uow.commit()
        await _run(env, push)
        assert push.sent == []

    async def test_no_notice_without_token_consent_or_after_a_log_today(
        self, env: ApiEnv, push: RecordingPush
    ) -> None:
        await signup(env, "a@example.com")  # no token
        no_consent = await signup(env, "b@example.com", meal_consent=False)
        logged = await signup(env, "c@example.com")
        await _register_token(env, no_consent, "ExponentPushToken[no-consent]")
        await _register_token(env, logged, "ExponentPushToken[logged]")
        assert (await post_meal(env, logged)).status_code == 201
        result = await _run(env, push)
        assert result["users_checked"] == 3
        assert push.sent == []

    async def test_paused_pet_gets_no_notice(self, env: ApiEnv, push: RecordingPush) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        await env.grant_premium(await env.user_id_for("ana@example.com"))
        paused = await env.client.post("/v1/pet/pause", json={"days": 3}, headers=headers)
        assert paused.status_code == 200, paused.text
        await _run(env, push)
        env.next_day()
        await _run(env, push)
        assert push.sent == []

    async def test_a_new_log_starts_a_new_episode(self, env: ApiEnv, push: RecordingPush) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        await _run(env, push)  # tired, episode 1
        assert (await post_meal(env, headers)).status_code == 201
        env.next_day()  # logged on day 1, nothing on day 2: tired again, new episode
        await _run(env, push)
        assert _kinds(push) == [NoticeKind.TIRED, NoticeKind.TIRED]

    async def test_every_device_gets_the_notice_and_dead_tokens_are_forgotten(
        self, env: ApiEnv
    ) -> None:
        push = RecordingPush(invalid_tokens={OTHER_TOKEN})
        headers = await signup(env)
        await _register_token(env, headers)
        await _register_token(env, headers, OTHER_TOKEN)
        await _run(env, push)
        assert [token for token, _, _ in push.sent] == [TOKEN]
        user_id = await env.user_id_for("ana@example.com")
        async with env.ctx.uow_factory() as uow:
            remaining = [t.token for t in await uow.push_tokens.list_for_user(user_id)]
        assert remaining == [TOKEN]

    async def test_push_outage_does_not_crash_or_resend(self, env: ApiEnv) -> None:
        headers = await signup(env)
        await _register_token(env, headers)
        result = await _run(env, RecordingPush(fail=True))
        assert result["failures"] == 0
        healthy = RecordingPush()
        await _run(env, healthy)
        assert healthy.sent == []  # recorded before sending: never delivered twice
