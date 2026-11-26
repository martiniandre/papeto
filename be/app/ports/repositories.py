"""Persistence ports: record dataclasses, repository Protocols and the UnitOfWork.

`app.db` implements them with SQLAlchemy; tests implement them in memory. Services only see
this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain import PetState, PointsReason


class ConsentType(StrEnum):
    TERMS_PRIVACY = "terms_privacy"
    MEAL_DATA = "meal_data"
    ANALYTICS = "analytics"


class DuplicateEmailError(Exception):
    """Raised by `UserRepository.add` when the email is already registered."""


@dataclass(frozen=True, slots=True)
class UserRecord:
    id: UUID
    email: str
    password_hash: str | None
    name: str
    timezone: str
    analytics_opt_out: bool
    adult_confirmed_at: datetime
    created_at: datetime
    deletion_requested_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    id: UUID
    user_id: UUID
    type: ConsentType
    version: str
    accepted: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PetRecord:
    id: UUID
    user_id: UUID
    name: str | None  # None until the user names the pet (screen 43)
    color: str
    state: PetState
    last_seen_lives: int | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PauseRecord:
    id: UUID
    user_id: UUID
    started_at: datetime
    ends_at: datetime


@dataclass(frozen=True, slots=True)
class MealRecord:
    id: UUID
    user_id: UUID
    logged_at: datetime
    local_day: date
    meal_type: str
    description: str
    items: list[str]
    food_groups: list[str]
    item_count: int
    colors: list[str]
    confidence: float
    plate_share: dict[str, float]
    new_foods: list[str]
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MealCursor:
    logged_at: datetime
    id: UUID


@dataclass(frozen=True, slots=True)
class PointsEventRecord:
    id: UUID
    user_id: UUID
    reason: PointsReason
    amount: int
    local_day: date
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PushTokenRecord:
    id: UUID
    user_id: UUID
    token: str
    platform: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SubscriptionRecord:
    id: UUID
    user_id: UUID
    provider: str
    status: str
    current_period_end: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PaymentEventRecord:
    id: UUID
    provider: str
    external_event_id: str
    event_type: str
    received_at: datetime
    processed: bool = False


@dataclass(frozen=True, slots=True)
class UserExport:
    """Everything stored about one user, for GET /me/export."""

    user: UserRecord
    consents: list[ConsentRecord] = field(default_factory=list)
    pet: PetRecord | None = None
    pauses: list[PauseRecord] = field(default_factory=list)
    meals: list[MealRecord] = field(default_factory=list)
    points: list[PointsEventRecord] = field(default_factory=list)
    subscription: SubscriptionRecord | None = None


class UserRepository(Protocol):
    async def add(self, user: UserRecord) -> None: ...
    async def get(self, user_id: UUID) -> UserRecord | None: ...
    async def get_by_email(self, email: str) -> UserRecord | None: ...
    async def save(self, user: UserRecord) -> None: ...


class ConsentRepository(Protocol):
    async def add(self, consent: ConsentRecord) -> None: ...
    async def latest_by_type(self, user_id: UUID) -> dict[ConsentType, ConsentRecord]: ...
    async def list_all(self, user_id: UUID) -> list[ConsentRecord]: ...


class PetRepository(Protocol):
    async def add(self, pet: PetRecord) -> None: ...
    async def get(self, user_id: UUID, *, for_update: bool = False) -> PetRecord | None: ...
    async def save(self, pet: PetRecord) -> None: ...


class PauseRepository(Protocol):
    async def add(self, pause: PauseRecord) -> None: ...
    async def list_for_user(self, user_id: UUID) -> list[PauseRecord]: ...
    async def end_active(self, user_id: UUID, now: datetime) -> None:
        """Set `ends_at = now` on every pause still running at `now`."""
        ...


class MealRepository(Protocol):
    async def add(self, meal: MealRecord) -> None: ...
    async def get(self, user_id: UUID, meal_id: UUID) -> MealRecord | None:
        """Only non-deleted meals."""
        ...

    async def save(self, meal: MealRecord) -> None: ...
    async def list_page(
        self, user_id: UUID, *, since_day: date, cursor: MealCursor | None, limit: int
    ) -> list[MealRecord]:
        """Non-deleted meals with `local_day >= since_day`, newest first, after `cursor`."""
        ...

    async def recent_items(self, user_id: UUID, since_day: date) -> set[str]:
        """Lowercased items of meals since `since_day` (deleted ones included)."""
        ...

    async def list_all(self, user_id: UUID) -> list[MealRecord]: ...


class PointsRepository(Protocol):
    async def add_many(self, events: list[PointsEventRecord]) -> None: ...
    async def total(self, user_id: UUID) -> int: ...
    async def count_on_day(self, user_id: UUID, reason: PointsReason, day: date) -> int: ...
    async def list_all(self, user_id: UUID) -> list[PointsEventRecord]: ...


class UsageRepository(Protocol):
    async def count(self, user_id: UUID, day: date) -> int:
        """Successful analyses on a local day."""
        ...

    async def increment(self, user_id: UUID, day: date) -> None: ...
    async def logged_days(self, user_id: UUID) -> set[date]: ...


class PushTokenRepository(Protocol):
    async def upsert(self, token: PushTokenRecord) -> None: ...
    async def list_for_user(self, user_id: UUID) -> list[PushTokenRecord]: ...


class SubscriptionRepository(Protocol):
    async def get(self, user_id: UUID) -> SubscriptionRecord | None: ...
    async def upsert(self, subscription: SubscriptionRecord) -> None: ...


class PaymentEventRepository(Protocol):
    async def add_if_new(self, event: PaymentEventRecord) -> bool:
        """False when `external_event_id` was already stored (duplicate webhook)."""
        ...


class UnitOfWork(Protocol):
    """One transaction. Repositories are read-only properties so adapters may narrow their types."""

    @property
    def users(self) -> UserRepository: ...
    @property
    def consents(self) -> ConsentRepository: ...
    @property
    def pets(self) -> PetRepository: ...
    @property
    def pauses(self) -> PauseRepository: ...
    @property
    def meals(self) -> MealRepository: ...
    @property
    def points(self) -> PointsRepository: ...
    @property
    def usage(self) -> UsageRepository: ...
    @property
    def push_tokens(self) -> PushTokenRepository: ...
    @property
    def subscriptions(self) -> SubscriptionRepository: ...
    @property
    def payment_events(self) -> PaymentEventRepository: ...

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Rolls back anything not committed."""
        ...

    async def commit(self) -> None: ...
