"""Test app builder: the real FastAPI app wired with fake adapters and any UnitOfWork factory."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

import httpx
from fastapi import FastAPI

from app.config import Settings
from app.container import Container
from app.main import create_app
from app.ports.repositories import SubscriptionRecord, UnitOfWork
from app.providers.fake_clock import FakeClock, SequentialIdGenerator
from app.providers.fake_misc import NoopAnalytics, NoopErrorReporter, RecordingEmail
from app.providers.fake_vision import FakeFoodVision
from app.providers.local_auth import LocalAuthProvider
from app.services.context import ServiceContext
from tests.support.builders import FAST_HASHER, JWT_SECRET, START

UowFactory = Callable[[], UnitOfWork]


@dataclass
class ApiEnv:
    app: FastAPI
    client: httpx.AsyncClient
    clock: FakeClock
    ctx: ServiceContext

    def next_day(self, days: int = 1) -> None:
        self.clock.advance(timedelta(days=days))

    async def grant_premium(self, user_id: UUID) -> None:
        async with self.ctx.uow_factory() as uow:
            await uow.subscriptions.upsert(
                SubscriptionRecord(
                    id=self.ctx.ids.new_id(),
                    user_id=user_id,
                    provider="fake",
                    status="active",
                    current_period_end=self.clock.now() + timedelta(days=30),
                    created_at=self.clock.now(),
                )
            )
            await uow.commit()

    async def user_id_for(self, email: str) -> UUID:
        async with self.ctx.uow_factory() as uow:
            user = await uow.users.get_by_email(email)
        assert user is not None
        return user.id


def build_env(uow_factory: UowFactory, *, max_upload_bytes: int = 1024 * 1024) -> ApiEnv:
    clock = FakeClock(START)
    ids = SequentialIdGenerator()
    ctx = ServiceContext(
        uow_factory=uow_factory,
        clock=clock,
        ids=ids,
        vision=FakeFoodVision(),
        auth=LocalAuthProvider(
            secret=JWT_SECRET,
            clock=clock,
            ids=ids,
            access_minutes=60 * 24 * 365,  # tests move the fake clock by days
            hasher=FAST_HASHER,
        ),
        analytics=NoopAnalytics(),
        error_reporter=NoopErrorReporter(),
        email=RecordingEmail(),
    )

    async def readiness() -> dict[str, bool]:
        return {"database": True, "redis": True}

    async def shutdown() -> None:
        return None

    settings = Settings(jwt_secret=JWT_SECRET, max_upload_bytes=max_upload_bytes, log_level="ERROR")  # type: ignore[arg-type]
    app = create_app(settings, Container(ctx=ctx, readiness=readiness, shutdown=shutdown))
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    return ApiEnv(app=app, client=client, clock=clock, ctx=ctx)
