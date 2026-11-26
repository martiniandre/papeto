"""Engine, session factory and the SQLAlchemy UnitOfWork."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.repositories import (
    SqlConsentRepository,
    SqlMealRepository,
    SqlNoticeRepository,
    SqlPasswordResetRepository,
    SqlPauseRepository,
    SqlPaymentEventRepository,
    SqlPetRepository,
    SqlPointsRepository,
    SqlPushTokenRepository,
    SqlRetentionRepository,
    SqlSubscriptionRepository,
    SqlUsageRepository,
    SqlUserRepository,
)


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


class SqlUnitOfWork:
    """One transaction per use case. Anything not committed is rolled back on exit."""

    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        session = self._factory()
        self._session = session
        self.users = SqlUserRepository(session)
        self.consents = SqlConsentRepository(session)
        self.pets = SqlPetRepository(session)
        self.pauses = SqlPauseRepository(session)
        self.meals = SqlMealRepository(session)
        self.points = SqlPointsRepository(session)
        self.usage = SqlUsageRepository(session)
        self.password_resets = SqlPasswordResetRepository(session)
        self.push_tokens = SqlPushTokenRepository(session)
        self.retention = SqlRetentionRepository(session)
        self.notices = SqlNoticeRepository(session)
        self.subscriptions = SqlSubscriptionRepository(session)
        self.payment_events = SqlPaymentEventRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            await self._session.rollback()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()


class SqlUowFactory:
    """Callable that returns a fresh UnitOfWork per use case."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._sessions = async_sessionmaker(engine, expire_on_commit=False)

    def __call__(self) -> SqlUnitOfWork:
        return SqlUnitOfWork(self._sessions)
