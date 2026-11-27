"""In-memory UnitOfWork for tests that do not need Postgres. No rollback: tests only inspect
committed outcomes, and use cases write nothing before their last failure point."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from app.domain import NoticeKind, PointsReason
from app.ports.repositories import (
    ConsentRecord,
    ConsentType,
    DuplicateEmailError,
    MealCursor,
    MealRecord,
    NoticeRecord,
    PasswordResetRecord,
    PauseRecord,
    PaymentEventRecord,
    PetRecord,
    PointsEventRecord,
    PushTokenRecord,
    SubscriptionRecord,
    UserRecord,
)


@dataclass
class MemoryStore:
    users: dict[UUID, UserRecord] = field(default_factory=dict)
    consents: list[ConsentRecord] = field(default_factory=list)
    pets: dict[UUID, PetRecord] = field(default_factory=dict)  # by user id
    pauses: list[PauseRecord] = field(default_factory=list)
    meals: dict[UUID, MealRecord] = field(default_factory=dict)
    points: list[PointsEventRecord] = field(default_factory=list)
    usage: dict[tuple[UUID, date], int] = field(default_factory=dict)
    manual_logs: dict[tuple[UUID, date], int] = field(default_factory=dict)
    password_resets: dict[str, PasswordResetRecord] = field(default_factory=dict)  # by hash
    push_tokens: dict[str, PushTokenRecord] = field(default_factory=dict)
    notices: list[NoticeRecord] = field(default_factory=list)
    subscriptions: dict[UUID, SubscriptionRecord] = field(default_factory=dict)
    payment_events: dict[str, PaymentEventRecord] = field(default_factory=dict)


class MemUsers:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add(self, user: UserRecord) -> None:
        if any(u.email == user.email for u in self.s.users.values()):
            raise DuplicateEmailError
        if self._subject_taken(user):
            raise DuplicateEmailError
        self.s.users[user.id] = user

    def _subject_taken(self, user: UserRecord) -> bool:
        return user.google_subject is not None and any(
            u.google_subject == user.google_subject and u.id != user.id
            for u in self.s.users.values()
        )

    async def get(self, user_id: UUID) -> UserRecord | None:
        user = self.s.users.get(user_id)
        return user if user is not None and user.anonymized_at is None else None

    async def get_by_email(self, email: str) -> UserRecord | None:
        return next((u for u in self.s.users.values() if u.email == email), None)

    async def get_by_google_subject(self, subject: str) -> UserRecord | None:
        return next(
            (
                u
                for u in self.s.users.values()
                if u.google_subject == subject and u.anonymized_at is None
            ),
            None,
        )

    async def save(self, user: UserRecord) -> None:
        if self._subject_taken(user):
            raise DuplicateEmailError
        self.s.users[user.id] = user

    async def list_notifiable_page(self, *, after: UUID | None, limit: int) -> list[UserRecord]:
        rows = sorted(
            (
                u
                for u in self.s.users.values()
                if u.deletion_requested_at is None and (after is None or u.id > after)
            ),
            key=lambda u: u.id,
        )
        return rows[:limit]


class MemConsents:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add(self, consent: ConsentRecord) -> None:
        self.s.consents.append(consent)

    async def list_all(self, user_id: UUID) -> list[ConsentRecord]:
        return [c for c in self.s.consents if c.user_id == user_id]

    async def latest_by_type(self, user_id: UUID) -> dict[ConsentType, ConsentRecord]:
        return {c.type: c for c in await self.list_all(user_id)}


class MemPets:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add(self, pet: PetRecord) -> None:
        self.s.pets[pet.user_id] = pet

    async def get(self, user_id: UUID, *, for_update: bool = False) -> PetRecord | None:
        return self.s.pets.get(user_id)

    async def save(self, pet: PetRecord) -> None:
        self.s.pets[pet.user_id] = pet


class MemPauses:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add(self, pause: PauseRecord) -> None:
        self.s.pauses.append(pause)

    async def list_for_user(self, user_id: UUID) -> list[PauseRecord]:
        return [p for p in self.s.pauses if p.user_id == user_id]

    async def end_active(self, user_id: UUID, now: datetime) -> None:
        self.s.pauses = [
            replace(p, ends_at=now)
            if p.user_id == user_id and p.started_at <= now < p.ends_at
            else p
            for p in self.s.pauses
        ]


class MemMeals:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add(self, meal: MealRecord) -> None:
        self.s.meals[meal.id] = meal

    async def get(self, user_id: UUID, meal_id: UUID) -> MealRecord | None:
        meal = self.s.meals.get(meal_id)
        if meal is None or meal.user_id != user_id or meal.deleted_at is not None:
            return None
        return meal

    async def save(self, meal: MealRecord) -> None:
        self.s.meals[meal.id] = meal

    async def list_page(
        self, user_id: UUID, *, since_day: date, cursor: MealCursor | None, limit: int
    ) -> list[MealRecord]:
        rows = [
            m
            for m in self.s.meals.values()
            if m.user_id == user_id and m.deleted_at is None and m.local_day >= since_day
        ]
        rows.sort(key=lambda m: (m.logged_at, m.id), reverse=True)
        if cursor is not None:
            rows = [m for m in rows if (m.logged_at, m.id) < (cursor.logged_at, cursor.id)]
        return rows[:limit]

    async def recent_items(self, user_id: UUID, since_day: date) -> set[str]:
        return {
            item.lower()
            for m in self.s.meals.values()
            if m.user_id == user_id and m.local_day >= since_day
            for item in m.items
        }

    async def delete_all(self, user_id: UUID) -> int:
        ids = [m.id for m in self.s.meals.values() if m.user_id == user_id]
        for meal_id in ids:
            del self.s.meals[meal_id]
        return len(ids)

    async def list_all(self, user_id: UUID) -> list[MealRecord]:
        return sorted(
            (m for m in self.s.meals.values() if m.user_id == user_id),
            key=lambda m: (m.logged_at, m.id),
        )


class MemPoints:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add_many(self, events: list[PointsEventRecord]) -> None:
        self.s.points.extend(events)

    async def total(self, user_id: UUID) -> int:
        return sum(e.amount for e in self.s.points if e.user_id == user_id)

    async def count_on_day(self, user_id: UUID, reason: PointsReason, day: date) -> int:
        return sum(
            1
            for e in self.s.points
            if e.user_id == user_id and e.reason == reason and e.local_day == day
        )

    async def list_all(self, user_id: UUID) -> list[PointsEventRecord]:
        return [e for e in self.s.points if e.user_id == user_id]


class MemUsage:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def count(self, user_id: UUID, day: date) -> int:
        return self.s.usage.get((user_id, day), 0)

    async def increment(self, user_id: UUID, day: date) -> None:
        self.s.usage[(user_id, day)] = self.s.usage.get((user_id, day), 0) + 1

    async def increment_manual(self, user_id: UUID, day: date) -> None:
        self.s.manual_logs[(user_id, day)] = self.s.manual_logs.get((user_id, day), 0) + 1

    async def logged_days(self, user_id: UUID) -> set[date]:
        counts = (*self.s.usage.items(), *self.s.manual_logs.items())
        return {day for (uid, day), n in counts if uid == user_id and n > 0}


class MemPasswordResets:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add(self, reset: PasswordResetRecord) -> None:
        self.s.password_resets[reset.token_hash] = reset

    async def get_by_hash(self, token_hash: str) -> PasswordResetRecord | None:
        return self.s.password_resets.get(token_hash)

    async def count_since(self, user_id: UUID, since: datetime) -> int:
        return sum(
            1
            for r in self.s.password_resets.values()
            if r.user_id == user_id and r.created_at >= since
        )

    async def use_all(self, user_id: UUID, now: datetime) -> None:
        for key, r in list(self.s.password_resets.items()):
            if r.user_id == user_id and r.used_at is None:
                self.s.password_resets[key] = replace(r, used_at=now)


class MemPushTokens:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def upsert(self, token: PushTokenRecord) -> None:
        self.s.push_tokens[token.token] = token

    async def list_for_user(self, user_id: UUID) -> list[PushTokenRecord]:
        return [t for t in self.s.push_tokens.values() if t.user_id == user_id]

    async def delete(self, user_id: UUID, token: str) -> None:
        current = self.s.push_tokens.get(token)
        if current is not None and current.user_id == user_id:
            del self.s.push_tokens[token]


class MemRetention:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def list_pending_deletion(self, cutoff: datetime, limit: int) -> list[UserRecord]:
        rows = [
            u
            for u in self.s.users.values()
            if u.anonymized_at is None
            and u.deletion_requested_at is not None
            and u.deletion_requested_at <= cutoff
        ]
        rows.sort(key=lambda u: (u.deletion_requested_at or cutoff, u.id))
        return rows[:limit]

    async def erase_personal_data(self, user: UserRecord) -> None:
        uid = user.id
        self.s.meals = {k: v for k, v in self.s.meals.items() if v.user_id != uid}
        self.s.points = [e for e in self.s.points if e.user_id != uid]
        self.s.pauses = [p for p in self.s.pauses if p.user_id != uid]
        self.s.pets.pop(uid, None)
        self.s.push_tokens = {k: v for k, v in self.s.push_tokens.items() if v.user_id != uid}
        self.s.notices = [n for n in self.s.notices if n.user_id != uid]
        self.s.usage = {k: v for k, v in self.s.usage.items() if k[0] != uid}
        self.s.users[uid] = user

    async def list_anonymized_before(self, cutoff: datetime, limit: int) -> list[UUID]:
        rows = sorted(
            (u for u in self.s.users.values() if u.anonymized_at and u.anonymized_at <= cutoff),
            key=lambda u: (u.anonymized_at or cutoff, u.id),
        )
        return [u.id for u in rows[:limit]]

    async def delete_user(self, user_id: UUID) -> None:
        self.s.users.pop(user_id, None)
        self.s.consents = [c for c in self.s.consents if c.user_id != user_id]
        self.s.subscriptions.pop(user_id, None)


class MemNotices:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def kinds_in_episode(self, user_id: UUID, episode_day: date) -> set[NoticeKind]:
        return {
            n.kind for n in self.s.notices if n.user_id == user_id and n.episode_day == episode_day
        }

    async def count_on_day(self, user_id: UUID, local_day: date) -> int:
        return sum(1 for n in self.s.notices if n.user_id == user_id and n.local_day == local_day)

    async def add_if_new(self, notice: NoticeRecord) -> bool:
        if any(
            n.user_id == notice.user_id
            and n.kind == notice.kind
            and n.episode_day == notice.episode_day
            for n in self.s.notices
        ):
            return False
        self.s.notices.append(notice)
        return True


class MemSubscriptions:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def get(self, user_id: UUID) -> SubscriptionRecord | None:
        return self.s.subscriptions.get(user_id)

    async def upsert(self, subscription: SubscriptionRecord) -> None:
        self.s.subscriptions[subscription.user_id] = subscription


class MemPaymentEvents:
    def __init__(self, s: MemoryStore) -> None:
        self.s = s

    async def add_if_new(self, event: PaymentEventRecord) -> bool:
        if event.external_event_id in self.s.payment_events:
            return False
        self.s.payment_events[event.external_event_id] = event
        return True


class MemoryUnitOfWork:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self.users = MemUsers(store)
        self.consents = MemConsents(store)
        self.pets = MemPets(store)
        self.pauses = MemPauses(store)
        self.meals = MemMeals(store)
        self.points = MemPoints(store)
        self.usage = MemUsage(store)
        self.password_resets = MemPasswordResets(store)
        self.push_tokens = MemPushTokens(store)
        self.retention = MemRetention(store)
        self.notices = MemNotices(store)
        self.subscriptions = MemSubscriptions(store)
        self.payment_events = MemPaymentEvents(store)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None


class MemoryUowFactory:
    def __init__(self) -> None:
        self.store = MemoryStore()

    def __call__(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.store)
