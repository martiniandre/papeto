"""Postgres for the integration suite.

If `TEST_DATABASE_URL` is set (e.g. `postgresql+asyncpg://user:pass@localhost:55432/papeto_test`),
the suite uses that existing database: migrations run to head and every test truncates all tables,
so point it only at a disposable test database. Otherwise it starts Postgres 16 via Testcontainers,
which needs a running Docker daemon.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.community.postgres import PostgresContainer

from alembic import command
from app.db.models import Base
from app.db.session import SqlUowFactory, create_engine
from tests.support.api_env import ApiEnv, build_env

BE_DIR = Path(__file__).parents[2]


@contextmanager
def _migrated(url: str) -> Iterator[str]:
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url  # alembic/env.py reads it
    try:
        config = Config(str(BE_DIR / "alembic.ini"))
        config.set_main_option("script_location", str(BE_DIR / "alembic"))
        command.upgrade(config, "head")
        yield url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    external = os.environ.get("TEST_DATABASE_URL")
    if external:
        with _migrated(external) as url:
            yield url
        return
    with (
        PostgresContainer("postgres:16-alpine", driver="asyncpg") as postgres,
        _migrated(postgres.get_connection_url()) as url,
    ):
        yield url


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    created = create_engine(database_url)
    async with created.begin() as connection:
        tables = ", ".join(f'"{name}"' for name in Base.metadata.tables)
        await connection.execute(text(f"TRUNCATE {tables} CASCADE"))
    yield created
    await created.dispose()


@pytest.fixture
async def uow_factory(engine: AsyncEngine) -> SqlUowFactory:
    return SqlUowFactory(engine)


@pytest.fixture
async def env(uow_factory: SqlUowFactory) -> AsyncIterator[ApiEnv]:
    built = build_env(uow_factory)
    yield built
    await built.client.aclose()
