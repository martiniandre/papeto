"""SQL repository behavior that only a real Postgres can prove (unverified without Docker)."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import command
from app.db.session import SqlUowFactory
from app.domain import PointsReason, new_pet
from app.ports.repositories import (
    AuthMethod,
    DuplicateEmailError,
    MealRecord,
    PaymentEventRecord,
    PetRecord,
    PointsEventRecord,
    UserRecord,
)
from tests.integration.conftest import BE_DIR

pytestmark = pytest.mark.integration

NOW = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
DAY = date(2026, 3, 10)


def _user(email: str = "a@example.com") -> UserRecord:
    return UserRecord(
        id=uuid4(),
        email=email,
        password_hash="hash",
        name="A",
        timezone="America/Sao_Paulo",
        analytics_opt_out=False,
        adult_confirmed_at=NOW,
        created_at=NOW,
    )


async def _add_user(factory: SqlUowFactory, user: UserRecord) -> None:
    async with factory() as uow:
        await uow.users.add(user)
        state = new_pet(DAY)
        await uow.pets.add(
            PetRecord(
                id=uuid4(),
                user_id=user.id,
                name="Bolinha",
                color="default",
                state=state,
                last_seen_lives=2,
                created_at=NOW,
            )
        )
        await uow.commit()


async def test_duplicate_email_is_reported(uow_factory: SqlUowFactory) -> None:
    await _add_user(uow_factory, _user())
    async with uow_factory() as uow:
        with pytest.raises(DuplicateEmailError):
            await uow.users.add(_user())


async def test_google_subject_roundtrip_and_uniqueness(uow_factory: SqlUowFactory) -> None:
    google = replace(
        _user("g@example.com"),
        password_hash=None,
        adult_confirmed_at=None,
        auth_provider=AuthMethod.GOOGLE,
        google_subject="sub-1",
    )
    await _add_user(uow_factory, google)
    async with uow_factory() as uow:
        found = await uow.users.get_by_google_subject("sub-1")
        assert found == google
        assert await uow.users.get_by_google_subject("sub-2") is None
    async with uow_factory() as uow:
        with pytest.raises(DuplicateEmailError):
            await uow.users.add(replace(_user("other@example.com"), google_subject="sub-1"))


async def test_linking_and_confirming_are_saved(uow_factory: SqlUowFactory) -> None:
    user = replace(_user(), adult_confirmed_at=None)
    taken = replace(_user("b@example.com"), google_subject="taken")
    await _add_user(uow_factory, user)
    await _add_user(uow_factory, taken)
    async with uow_factory() as uow:
        await uow.users.save(replace(user, google_subject="sub-9", adult_confirmed_at=NOW))
        await uow.commit()
    async with uow_factory() as uow:
        saved = await uow.users.get(user.id)
        assert saved is not None
        assert (saved.google_subject, saved.adult_confirmed_at) == ("sub-9", NOW)
        assert saved.auth_provider is AuthMethod.EMAIL
    async with uow_factory() as uow:
        with pytest.raises(DuplicateEmailError):
            await uow.users.save(replace(user, google_subject="taken"))


async def test_payment_event_is_idempotent_by_external_event_id(uow_factory: SqlUowFactory) -> None:
    event = PaymentEventRecord(
        id=uuid4(), provider="stripe", external_event_id="evt_1", event_type="x", received_at=NOW
    )
    async with uow_factory() as uow:
        assert await uow.payment_events.add_if_new(event) is True
        await uow.commit()
    async with uow_factory() as uow:
        again = PaymentEventRecord(
            id=uuid4(),
            provider="stripe",
            external_event_id="evt_1",
            event_type="x",
            received_at=NOW,
        )
        assert await uow.payment_events.add_if_new(again) is False


async def test_points_events_must_be_positive(uow_factory: SqlUowFactory) -> None:
    user = _user()
    await _add_user(uow_factory, user)
    async with uow_factory() as uow:
        with pytest.raises(IntegrityError):
            await uow.points.add_many(
                [
                    PointsEventRecord(
                        id=uuid4(),
                        user_id=user.id,
                        reason=PointsReason.MEAL_LOGGED,
                        amount=-5,
                        local_day=DAY,
                        created_at=NOW,
                    )
                ]
            )


async def test_usage_increment_is_atomic_under_concurrency(uow_factory: SqlUowFactory) -> None:
    user = _user()
    await _add_user(uow_factory, user)

    async def bump() -> None:
        async with uow_factory() as uow:
            await uow.usage.increment(user.id, DAY)
            await uow.commit()

    await asyncio.gather(*(bump() for _ in range(5)))
    async with uow_factory() as uow:
        assert await uow.usage.count(user.id, DAY) == 5
        assert await uow.usage.logged_days(user.id) == {DAY}


async def test_meal_pagination_orders_by_time_then_id(uow_factory: SqlUowFactory) -> None:
    user = _user()
    await _add_user(uow_factory, user)
    async with uow_factory() as uow:
        for index in range(3):
            await uow.meals.add(
                MealRecord(
                    id=uuid4(),
                    user_id=user.id,
                    logged_at=NOW,  # same instant on purpose: the id breaks the tie
                    local_day=DAY,
                    meal_type="lunch",
                    description=f"meal {index}",
                    items=["rice"],
                    food_groups=["grains"],
                    item_count=1,
                    colors=[],
                    confidence=0.5,
                    plate_share={"grains": 1.0},
                    new_foods=[],
                )
            )
        await uow.commit()
    async with uow_factory() as uow:
        first = await uow.meals.list_page(user.id, since_day=DAY, cursor=None, limit=2)
        assert len(first) == 2
        from app.ports.repositories import MealCursor

        rest = await uow.meals.list_page(
            user.id,
            since_day=DAY,
            cursor=MealCursor(first[-1].logged_at, first[-1].id),
            limit=5,
        )
        assert len(rest) == 1
        assert {m.id for m in [*first, *rest]} == {m.id for m in await uow.meals.list_all(user.id)}


async def test_migration_downgrade_and_upgrade_again(
    engine: AsyncEngine, database_url: str
) -> None:
    config = Config(str(BE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BE_DIR / "alembic"))
    await asyncio.to_thread(command.downgrade, config, "base")
    async with engine.connect() as connection:
        tables = (
            await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
        ).scalars()
        assert set(tables) <= {"alembic_version"}
    await asyncio.to_thread(command.upgrade, config, "head")


async def test_migration_downgrade_refuses_to_invent_adult_confirmation(
    engine: AsyncEngine, uow_factory: SqlUowFactory, database_url: str
) -> None:
    await _add_user(uow_factory, replace(_user(), adult_confirmed_at=None))
    config = Config(str(BE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BE_DIR / "alembic"))
    with pytest.raises(RuntimeError, match="adult confirmation"):
        await asyncio.to_thread(command.downgrade, config, "0009_pet_attributes")
    async with engine.connect() as connection:
        version = (
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
    assert version == "0010_google_sign_in"
