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

from app.domain import DEFAULT_PREFS, NoticeKind, NotificationPrefs, PetState, PointsReason


class ConsentType(StrEnum):
    TERMS_PRIVACY = "terms_privacy"
    MEAL_DATA = "meal_data"
    ANALYTICS = "analytics"


class MealSource(StrEnum):
    PHOTO = "photo"  # described by the vision provider
    MANUAL = "manual"  # items chosen by hand when the photo could not be read (RF-95)


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
    notifications: NotificationPrefs = DEFAULT_PREFS
    anonymized_at: datetime | None = None


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
    source: MealSource = MealSource.PHOTO
    # Who analyzed the photo (None for manual meals and rows from before migration 0008).
    vision_provider: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None


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
class PasswordResetRecord:
    """A single-use reset token. Only its SHA-256 hash is stored, never the token itself."""

    id: UUID
    user_id: UUID
    token_hash: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PushTokenRecord:
    id: UUID
    user_id: UUID
    token: str
    platform: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NoticeRecord:
    """A notice that was decided and sent. `episode_day` is the stretch since the last log."""

    id: UUID
    user_id: UUID
    kind: NoticeKind
    episode_day: date
    local_day: date
    sent_at: datetime


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
    async def get(self, user_id: UUID) -> UserRecord | None:
        """None for unknown and for anonymized accounts (they are gone for every use case)."""
        ...

    async def get_by_email(self, email: str) -> UserRecord | None: ...
    async def save(self, user: UserRecord) -> None: ...
    async def list_notifiable_page(self, *, after: UUID | None, limit: int) -> list[UserRecord]:
        """Users not pending deletion, ordered by id, strictly after `after`."""
        ...


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
        """Successful photo analyses on a local day (the AI limit). Manual logs never count."""
        ...

    async def increment(self, user_id: UUID, day: date) -> None:
        """Record one successful photo analysis."""
        ...

    async def increment_manual(self, user_id: UUID, day: date) -> None:
        """Record one manual log: a logged day that does not consume the AI limit."""
        ...

    async def logged_days(self, user_id: UUID) -> set[date]:
        """Days with at least one photo analysis or manual log."""
        ...


class PasswordResetRepository(Protocol):
    async def add(self, reset: PasswordResetRecord) -> None: ...
    async def get_by_hash(self, token_hash: str) -> PasswordResetRecord | None: ...
    async def count_since(self, user_id: UUID, since: datetime) -> int:
        """Tokens created for the user at or after `since` (used ones included)."""
        ...

    async def use_all(self, user_id: UUID, now: datetime) -> None:
        """Set `used_at = now` on every unused token of the user."""
        ...


class PushTokenRepository(Protocol):
    async def upsert(self, token: PushTokenRecord) -> None:
        """Register or refresh. A token seen again moves to the user that sent it last."""
        ...

    async def list_for_user(self, user_id: UUID) -> list[PushTokenRecord]: ...
    async def delete(self, user_id: UUID, token: str) -> None:
        """Remove the user's own token. Idempotent: a missing token is not an error."""
        ...


class RetentionRepository(Protocol):
    """Account lifecycle after a deletion request: 30 days pending, then erase, keep legal rows."""

    async def list_pending_deletion(self, cutoff: datetime, limit: int) -> list[UserRecord]:
        """Not yet anonymized users whose deletion was requested at or before `cutoff`."""
        ...

    async def erase_personal_data(self, user: UserRecord) -> None:
        """Delete meals, points, pause history, pet, push tokens, notice log and usage, and
        store the anonymized `user` row. Consents and the subscription stay (legal retention)."""
        ...

    async def list_anonymized_before(self, cutoff: datetime, limit: int) -> list[UUID]:
        """Ids of users anonymized at or before `cutoff` (legal retention has ended)."""
        ...

    async def delete_user(self, user_id: UUID) -> None:
        """Remove the user row and everything still attached (consents, subscription)."""
        ...


class NoticeRepository(Protocol):
    async def kinds_in_episode(self, user_id: UUID, episode_day: date) -> set[NoticeKind]: ...
    async def count_on_day(self, user_id: UUID, local_day: date) -> int: ...
    async def add_if_new(self, notice: NoticeRecord) -> bool:
        """False when this (user, kind, episode) already has a notice: nothing is sent twice."""
        ...


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
    def password_resets(self) -> PasswordResetRepository: ...
    @property
    def push_tokens(self) -> PushTokenRepository: ...
    @property
    def retention(self) -> RetentionRepository: ...
    @property
    def notices(self) -> NoticeRepository: ...
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
