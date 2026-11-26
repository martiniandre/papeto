"""Forgot and reset password against the in-memory UnitOfWork and the recording email fake."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.providers.fake_misc import RecordingEmail
from app.services import auth as auth_service
from app.services.errors import InvalidCredentials, InvalidResetToken
from app.services.password_reset import (
    hash_reset_token,
    request_password_reset,
    reset_link,
    reset_password,
)
from tests.support.builders import World, make_user, make_world

NEW_PASSWORD = "brand-new-pass-2"


def outbox(world: World) -> RecordingEmail:
    assert isinstance(world.ctx.email, RecordingEmail)
    return world.ctx.email


def token_from(body: str) -> str:
    link = next(line for line in body.splitlines() if "token=" in line)
    return parse_qs(urlparse(link.strip()).query)["token"][0]


async def test_unknown_email_sends_nothing_and_does_not_fail() -> None:
    world = make_world()
    await make_user(world)
    await request_password_reset(world.ctx, email="nobody@example.com")
    assert outbox(world).sent == []
    assert world.factory.store.password_resets == {}


async def test_reset_flow_changes_password_and_token_is_single_use() -> None:
    world = make_world()
    await make_user(world)
    await request_password_reset(world.ctx, email="  ANA@example.com ")
    [(to, subject, body)] = outbox(world).sent
    assert to == "ana@example.com"
    assert subject
    token = token_from(body)
    [stored] = world.factory.store.password_resets.values()
    assert stored.token_hash == hash_reset_token(token)
    assert token not in stored.token_hash  # only the hash is stored

    await reset_password(world.ctx, token=token, new_password=NEW_PASSWORD)
    assert await auth_service.login(world.ctx, email="ana@example.com", password=NEW_PASSWORD)
    with pytest.raises(InvalidCredentials):
        await auth_service.login(world.ctx, email="ana@example.com", password="correct-horse-1")
    with pytest.raises(InvalidResetToken):
        await reset_password(world.ctx, token=token, new_password="another-pass-3")


async def test_expired_and_unknown_tokens_are_rejected() -> None:
    world = make_world()
    await make_user(world)
    await request_password_reset(world.ctx, email="ana@example.com")
    token = token_from(outbox(world).sent[0][2])
    world.clock.advance(timedelta(minutes=world.ctx.password_reset_minutes))
    with pytest.raises(InvalidResetToken):
        await reset_password(world.ctx, token=token, new_password=NEW_PASSWORD)
    with pytest.raises(InvalidResetToken):
        await reset_password(world.ctx, token="not-a-token", new_password=NEW_PASSWORD)


async def test_token_works_until_just_before_expiry() -> None:
    world = make_world()
    await make_user(world)
    await request_password_reset(world.ctx, email="ana@example.com")
    token = token_from(outbox(world).sent[0][2])
    world.clock.advance(timedelta(minutes=world.ctx.password_reset_minutes, seconds=-1))
    await reset_password(world.ctx, token=token, new_password=NEW_PASSWORD)


async def test_using_one_token_invalidates_the_others() -> None:
    world = make_world()
    await make_user(world)
    await request_password_reset(world.ctx, email="ana@example.com")
    await request_password_reset(world.ctx, email="ana@example.com")
    first, second = (token_from(body) for _, _, body in outbox(world).sent)
    await reset_password(world.ctx, token=second, new_password=NEW_PASSWORD)
    with pytest.raises(InvalidResetToken):
        await reset_password(world.ctx, token=first, new_password="another-pass-3")


async def test_requests_above_the_hourly_cap_are_dropped_silently() -> None:
    world = make_world()
    await make_user(world)
    cap = world.ctx.password_reset_max_per_hour
    for _ in range(cap + 2):
        await request_password_reset(world.ctx, email="ana@example.com")
    assert len(outbox(world).sent) == cap
    world.clock.advance(timedelta(hours=1, seconds=1))
    await request_password_reset(world.ctx, email="ana@example.com")
    assert len(outbox(world).sent) == cap + 1


async def test_email_failure_is_reported_not_raised() -> None:
    class BrokenEmail:
        async def send(self, to: str, subject: str, body: str) -> None:
            raise ConnectionError("smtp down")

    class Capture:
        def __init__(self) -> None:
            self.errors: list[BaseException] = []

        def capture(self, error: BaseException) -> None:
            self.errors.append(error)

    world = make_world()
    await make_user(world)
    reporter = Capture()
    world.ctx = replace(world.ctx, email=BrokenEmail(), error_reporter=reporter)
    await request_password_reset(world.ctx, email="ana@example.com")
    assert [type(e) for e in reporter.errors] == [ConnectionError]


def test_reset_link_appends_the_token_as_a_query_parameter() -> None:
    assert reset_link("papeto://reset-password", "a+b") == "papeto://reset-password?token=a%2Bb"
    assert reset_link("https://x.test/r?lang=pt", "t") == "https://x.test/r?lang=pt&token=t"
