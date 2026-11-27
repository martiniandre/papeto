"""Builders shared by service and API tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from argon2 import PasswordHasher

from app.ports.repositories import ConsentType, SubscriptionRecord, UnitOfWork
from app.providers.fake_clock import FakeClock, SequentialIdGenerator
from app.providers.fake_google import FakeGoogleIdentity, new_rsa_key
from app.providers.fake_misc import NoopAnalytics, NoopErrorReporter, RecordingEmail
from app.providers.fake_vision import FakeFoodVision
from app.providers.local_auth import LocalAuthProvider
from app.services.auth import register
from app.services.consents import record_consent
from app.services.context import ServiceContext
from tests.support.memory import MemoryUowFactory

# 2026-03-10 12:00 UTC is 09:00 in Sao Paulo (same local day).
START = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
PHOTO = b"\xff\xd8\xff fake jpeg bytes"
JWT_SECRET = "test-secret-with-more-than-32-characters"
FAST_HASHER = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
_GOOGLE_KEY = new_rsa_key()  # RSA generation is slow; one key for the whole test run


def fake_google() -> FakeGoogleIdentity:
    """A fresh fake Google identity (own outage flag and fetch count) sharing the test key."""
    return FakeGoogleIdentity(private_key=_GOOGLE_KEY)


@dataclass
class World:
    ctx: ServiceContext
    clock: FakeClock
    factory: MemoryUowFactory

    def uow(self) -> UnitOfWork:
        return self.factory()

    def next_day(self, days: int = 1) -> None:
        self.clock.advance(timedelta(days=days))


def make_world(uow_factory: MemoryUowFactory | None = None) -> World:
    clock = FakeClock(START)
    ids = SequentialIdGenerator()
    factory = uow_factory or MemoryUowFactory()
    ctx = ServiceContext(
        uow_factory=factory,
        clock=clock,
        ids=ids,
        vision=FakeFoodVision(),
        auth=LocalAuthProvider(
            secret=JWT_SECRET,
            clock=clock,
            ids=ids,
            access_minutes=60 * 24 * 365,  # tests move the fake clock by days
            hasher=FAST_HASHER,
            google=fake_google().verifier(clock),
        ),
        analytics=NoopAnalytics(),
        error_reporter=NoopErrorReporter(),
        email=RecordingEmail(),
    )
    return World(ctx=ctx, clock=clock, factory=factory)


async def make_user(
    world: World, *, email: str = "ana@example.com", meal_consent: bool = True
) -> UUID:
    await register(
        world.ctx,
        email=email,
        password="correct-horse-1",
        name="Ana",
        timezone="America/Sao_Paulo",
        adult_confirmed=True,
    )
    user_id = next(u.id for u in world.factory.store.users.values() if u.email == email)
    if meal_consent:
        await record_consent(
            world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=True
        )
    return user_id


async def make_premium(world: World, user_id: UUID) -> None:
    async with world.uow() as uow:
        await uow.subscriptions.upsert(
            SubscriptionRecord(
                id=world.ctx.ids.new_id(),
                user_id=user_id,
                provider="fake",
                status="active",
                current_period_end=world.clock.now() + timedelta(days=30),
                created_at=world.clock.now(),
            )
        )
        await uow.commit()
