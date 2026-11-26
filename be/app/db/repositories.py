"""SQLAlchemy implementations of the repository ports in `app.ports.repositories`."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models as m
from app.domain import NoticeKind, NotificationPrefs, PetState, PointsReason
from app.ports.repositories import (
    ConsentRecord,
    ConsentType,
    DuplicateEmailError,
    MealCursor,
    MealRecord,
    NoticeRecord,
    PauseRecord,
    PaymentEventRecord,
    PetRecord,
    PointsEventRecord,
    PushTokenRecord,
    SubscriptionRecord,
    UserRecord,
)


def _user(row: m.UserModel) -> UserRecord:
    return UserRecord(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        name=row.name,
        timezone=row.timezone,
        analytics_opt_out=row.analytics_opt_out,
        adult_confirmed_at=row.adult_confirmed_at,
        created_at=row.created_at,
        deletion_requested_at=row.deletion_requested_at,
        notifications=NotificationPrefs(
            meal_reminder=row.notify_meal_reminder,
            sleepy_notice=row.notify_sleepy,
            weekly_summary=row.notify_weekly_summary,
            quiet_hours_start=row.quiet_hours_start,
            quiet_hours_end=row.quiet_hours_end,
        ),
    )


def _apply_prefs(row: m.UserModel, prefs: NotificationPrefs) -> None:
    row.notify_meal_reminder = prefs.meal_reminder
    row.notify_sleepy = prefs.sleepy_notice
    row.notify_weekly_summary = prefs.weekly_summary
    row.quiet_hours_start = prefs.quiet_hours_start
    row.quiet_hours_end = prefs.quiet_hours_end


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, user: UserRecord) -> None:
        row = m.UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            name=user.name,
            timezone=user.timezone,
            analytics_opt_out=user.analytics_opt_out,
            adult_confirmed_at=user.adult_confirmed_at,
            created_at=user.created_at,
            deletion_requested_at=user.deletion_requested_at,
        )
        _apply_prefs(row, user.notifications)
        self._s.add(row)
        try:
            await self._s.flush()
        except IntegrityError as exc:
            raise DuplicateEmailError from exc

    async def get(self, user_id: UUID) -> UserRecord | None:
        row = await self._s.get(m.UserModel, user_id)
        return _user(row) if row else None

    async def get_by_email(self, email: str) -> UserRecord | None:
        row = (
            await self._s.execute(select(m.UserModel).where(m.UserModel.email == email))
        ).scalar_one_or_none()
        return _user(row) if row else None

    async def save(self, user: UserRecord) -> None:
        row = await self._s.get(m.UserModel, user.id)
        if row is None:
            raise LookupError("user not found")
        row.name = user.name
        row.timezone = user.timezone
        row.analytics_opt_out = user.analytics_opt_out
        row.deletion_requested_at = user.deletion_requested_at
        row.password_hash = user.password_hash
        _apply_prefs(row, user.notifications)
        await self._s.flush()

    async def list_notifiable_page(self, *, after: UUID | None, limit: int) -> list[UserRecord]:
        stmt = select(m.UserModel).where(m.UserModel.deletion_requested_at.is_(None))
        if after is not None:
            stmt = stmt.where(m.UserModel.id > after)
        rows = await self._s.execute(stmt.order_by(m.UserModel.id).limit(limit))
        return [_user(row) for row in rows.scalars()]


def _consent(row: m.ConsentModel) -> ConsentRecord:
    return ConsentRecord(
        id=row.id,
        user_id=row.user_id,
        type=ConsentType(row.type),
        version=row.version,
        accepted=row.accepted,
        created_at=row.created_at,
    )


class SqlConsentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, consent: ConsentRecord) -> None:
        self._s.add(
            m.ConsentModel(
                id=consent.id,
                user_id=consent.user_id,
                type=consent.type.value,
                version=consent.version,
                accepted=consent.accepted,
                created_at=consent.created_at,
            )
        )
        await self._s.flush()

    async def list_all(self, user_id: UUID) -> list[ConsentRecord]:
        rows = await self._s.execute(
            select(m.ConsentModel)
            .where(m.ConsentModel.user_id == user_id)
            .order_by(m.ConsentModel.created_at, m.ConsentModel.id)
        )
        return [_consent(row) for row in rows.scalars()]

    async def latest_by_type(self, user_id: UUID) -> dict[ConsentType, ConsentRecord]:
        latest: dict[ConsentType, ConsentRecord] = {}
        for record in await self.list_all(user_id):
            latest[record.type] = record  # ordered oldest to newest, so the last one wins
        return latest


def _pet(row: m.PetModel) -> PetRecord:
    return PetRecord(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        color=row.color,
        state=PetState(
            lives=row.lives,
            streak_days=row.streak_days,
            last_log_day=row.last_log_day,
            settled_on=row.settled_on,
            rest_until=row.rest_until,
        ),
        last_seen_lives=row.last_seen_lives,
        created_at=row.created_at,
    )


def _apply_pet(row: m.PetModel, pet: PetRecord) -> None:
    row.name = pet.name
    row.color = pet.color
    row.lives = pet.state.lives
    row.streak_days = pet.state.streak_days
    row.last_log_day = pet.state.last_log_day
    row.settled_on = pet.state.settled_on
    row.rest_until = pet.state.rest_until
    row.last_seen_lives = pet.last_seen_lives


class SqlPetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, pet: PetRecord) -> None:
        row = m.PetModel(
            id=pet.id, user_id=pet.user_id, created_at=pet.created_at, name="", color="", lives=0
        )
        _apply_pet(row, pet)
        self._s.add(row)
        await self._s.flush()

    async def get(self, user_id: UUID, *, for_update: bool = False) -> PetRecord | None:
        stmt = select(m.PetModel).where(m.PetModel.user_id == user_id)
        if for_update:
            stmt = stmt.with_for_update()  # serializes concurrent logs for the same user
        row = (await self._s.execute(stmt)).scalar_one_or_none()
        return _pet(row) if row else None

    async def save(self, pet: PetRecord) -> None:
        row = await self._s.get(m.PetModel, pet.id)
        if row is None:
            raise LookupError("pet not found")
        _apply_pet(row, pet)
        await self._s.flush()


class SqlPauseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, pause: PauseRecord) -> None:
        self._s.add(
            m.PauseModel(
                id=pause.id,
                user_id=pause.user_id,
                started_at=pause.started_at,
                ends_at=pause.ends_at,
            )
        )
        await self._s.flush()

    async def list_for_user(self, user_id: UUID) -> list[PauseRecord]:
        rows = await self._s.execute(
            select(m.PauseModel)
            .where(m.PauseModel.user_id == user_id)
            .order_by(m.PauseModel.started_at)
        )
        return [
            PauseRecord(id=r.id, user_id=r.user_id, started_at=r.started_at, ends_at=r.ends_at)
            for r in rows.scalars()
        ]

    async def end_active(self, user_id: UUID, now: datetime) -> None:
        await self._s.execute(
            update(m.PauseModel)
            .where(
                m.PauseModel.user_id == user_id,
                m.PauseModel.started_at <= now,
                m.PauseModel.ends_at > now,
            )
            .values(ends_at=now)
        )


def _meal(row: m.MealLogModel) -> MealRecord:
    return MealRecord(
        id=row.id,
        user_id=row.user_id,
        logged_at=row.logged_at,
        local_day=row.local_day,
        meal_type=row.meal_type,
        description=row.description,
        items=list(row.items),
        food_groups=list(row.food_groups),
        item_count=row.item_count,
        colors=list(row.colors),
        confidence=row.confidence,
        plate_share=dict(row.plate_share),
        new_foods=list(row.new_foods),
        deleted_at=row.deleted_at,
    )


def _apply_meal(row: m.MealLogModel, meal: MealRecord) -> None:
    row.logged_at = meal.logged_at
    row.local_day = meal.local_day
    row.meal_type = meal.meal_type
    row.description = meal.description
    row.items = list(meal.items)
    row.food_groups = list(meal.food_groups)
    row.item_count = meal.item_count
    row.colors = list(meal.colors)
    row.confidence = meal.confidence
    row.plate_share = dict(meal.plate_share)
    row.new_foods = list(meal.new_foods)
    row.deleted_at = meal.deleted_at


class SqlMealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, meal: MealRecord) -> None:
        row = m.MealLogModel(id=meal.id, user_id=meal.user_id)
        _apply_meal(row, meal)
        self._s.add(row)
        await self._s.flush()

    async def get(self, user_id: UUID, meal_id: UUID) -> MealRecord | None:
        row = (
            await self._s.execute(
                select(m.MealLogModel).where(
                    m.MealLogModel.id == meal_id,
                    m.MealLogModel.user_id == user_id,
                    m.MealLogModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        return _meal(row) if row else None

    async def save(self, meal: MealRecord) -> None:
        row = await self._s.get(m.MealLogModel, meal.id)
        if row is None:
            raise LookupError("meal not found")
        _apply_meal(row, meal)
        await self._s.flush()

    async def list_page(
        self, user_id: UUID, *, since_day: date, cursor: MealCursor | None, limit: int
    ) -> list[MealRecord]:
        stmt = select(m.MealLogModel).where(
            m.MealLogModel.user_id == user_id,
            m.MealLogModel.deleted_at.is_(None),
            m.MealLogModel.local_day >= since_day,
        )
        if cursor is not None:
            stmt = stmt.where(
                or_(
                    m.MealLogModel.logged_at < cursor.logged_at,
                    and_(
                        m.MealLogModel.logged_at == cursor.logged_at,
                        m.MealLogModel.id < cursor.id,
                    ),
                )
            )
        stmt = stmt.order_by(m.MealLogModel.logged_at.desc(), m.MealLogModel.id.desc()).limit(limit)
        return [_meal(row) for row in (await self._s.execute(stmt)).scalars()]

    async def recent_items(self, user_id: UUID, since_day: date) -> set[str]:
        rows = await self._s.execute(
            select(m.MealLogModel.items).where(
                m.MealLogModel.user_id == user_id, m.MealLogModel.local_day >= since_day
            )
        )
        return {item.lower() for items in rows.scalars() for item in items}

    async def list_all(self, user_id: UUID) -> list[MealRecord]:
        rows = await self._s.execute(
            select(m.MealLogModel)
            .where(m.MealLogModel.user_id == user_id)
            .order_by(m.MealLogModel.logged_at, m.MealLogModel.id)
        )
        return [_meal(row) for row in rows.scalars()]


def _points(row: m.PointsEventModel) -> PointsEventRecord:
    return PointsEventRecord(
        id=row.id,
        user_id=row.user_id,
        reason=PointsReason(row.reason),
        amount=row.amount,
        local_day=row.local_day,
        created_at=row.created_at,
    )


class SqlPointsRepository:
    """Append-only: there is no update or delete method on purpose."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add_many(self, events: list[PointsEventRecord]) -> None:
        self._s.add_all(
            m.PointsEventModel(
                id=e.id,
                user_id=e.user_id,
                reason=e.reason.value,
                amount=e.amount,
                local_day=e.local_day,
                created_at=e.created_at,
            )
            for e in events
        )
        await self._s.flush()

    async def total(self, user_id: UUID) -> int:
        value = await self._s.scalar(
            select(func.coalesce(func.sum(m.PointsEventModel.amount), 0)).where(
                m.PointsEventModel.user_id == user_id
            )
        )
        return int(value or 0)

    async def count_on_day(self, user_id: UUID, reason: PointsReason, day: date) -> int:
        value = await self._s.scalar(
            select(func.count())
            .select_from(m.PointsEventModel)
            .where(
                m.PointsEventModel.user_id == user_id,
                m.PointsEventModel.reason == reason.value,
                m.PointsEventModel.local_day == day,
            )
        )
        return int(value or 0)

    async def list_all(self, user_id: UUID) -> list[PointsEventRecord]:
        rows = await self._s.execute(
            select(m.PointsEventModel)
            .where(m.PointsEventModel.user_id == user_id)
            .order_by(m.PointsEventModel.created_at, m.PointsEventModel.id)
        )
        return [_points(row) for row in rows.scalars()]


class SqlUsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def count(self, user_id: UUID, day: date) -> int:
        value = await self._s.scalar(
            select(m.DailyUsageModel.analyses).where(
                m.DailyUsageModel.user_id == user_id, m.DailyUsageModel.local_day == day
            )
        )
        return int(value or 0)

    async def increment(self, user_id: UUID, day: date) -> None:
        stmt = pg_insert(m.DailyUsageModel).values(user_id=user_id, local_day=day, analyses=1)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "local_day"],
            set_={"analyses": m.DailyUsageModel.analyses + 1},
        )
        await self._s.execute(stmt)

    async def logged_days(self, user_id: UUID) -> set[date]:
        rows = await self._s.execute(
            select(m.DailyUsageModel.local_day).where(
                m.DailyUsageModel.user_id == user_id, m.DailyUsageModel.analyses > 0
            )
        )
        return set(rows.scalars())


class SqlPushTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def upsert(self, token: PushTokenRecord) -> None:
        stmt = pg_insert(m.PushTokenModel).values(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            platform=token.platform,
            created_at=token.created_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["token"],
            set_={"user_id": token.user_id, "platform": token.platform},
        )
        await self._s.execute(stmt)

    async def list_for_user(self, user_id: UUID) -> list[PushTokenRecord]:
        rows = await self._s.execute(
            select(m.PushTokenModel).where(m.PushTokenModel.user_id == user_id)
        )
        return [
            PushTokenRecord(
                id=r.id,
                user_id=r.user_id,
                token=r.token,
                platform=r.platform,
                created_at=r.created_at,
            )
            for r in rows.scalars()
        ]

    async def delete(self, user_id: UUID, token: str) -> None:
        await self._s.execute(
            delete(m.PushTokenModel).where(
                m.PushTokenModel.user_id == user_id, m.PushTokenModel.token == token
            )
        )


class SqlNoticeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def kinds_in_episode(self, user_id: UUID, episode_day: date) -> set[NoticeKind]:
        rows = await self._s.execute(
            select(m.NoticeLogModel.kind).where(
                m.NoticeLogModel.user_id == user_id, m.NoticeLogModel.episode_day == episode_day
            )
        )
        return {NoticeKind(kind) for kind in rows.scalars()}

    async def count_on_day(self, user_id: UUID, local_day: date) -> int:
        value = await self._s.scalar(
            select(func.count())
            .select_from(m.NoticeLogModel)
            .where(m.NoticeLogModel.user_id == user_id, m.NoticeLogModel.local_day == local_day)
        )
        return int(value or 0)

    async def add_if_new(self, notice: NoticeRecord) -> bool:
        stmt = (
            pg_insert(m.NoticeLogModel)
            .values(
                id=notice.id,
                user_id=notice.user_id,
                kind=notice.kind.value,
                episode_day=notice.episode_day,
                local_day=notice.local_day,
                sent_at=notice.sent_at,
            )
            .on_conflict_do_nothing(constraint="uq_notice_log_episode")
            .returning(m.NoticeLogModel.id)
        )
        return (await self._s.execute(stmt)).scalar_one_or_none() is not None


class SqlSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, user_id: UUID) -> SubscriptionRecord | None:
        row = (
            await self._s.execute(
                select(m.SubscriptionModel).where(m.SubscriptionModel.user_id == user_id)
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return SubscriptionRecord(
            id=row.id,
            user_id=row.user_id,
            provider=row.provider,
            status=row.status,
            current_period_end=row.current_period_end,
            created_at=row.created_at,
        )

    async def upsert(self, subscription: SubscriptionRecord) -> None:
        stmt = pg_insert(m.SubscriptionModel).values(
            id=subscription.id,
            user_id=subscription.user_id,
            provider=subscription.provider,
            status=subscription.status,
            current_period_end=subscription.current_period_end,
            created_at=subscription.created_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "provider": subscription.provider,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
            },
        )
        await self._s.execute(stmt)


class SqlPaymentEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add_if_new(self, event: PaymentEventRecord) -> bool:
        stmt = (
            pg_insert(m.PaymentEventModel)
            .values(
                id=event.id,
                provider=event.provider,
                external_event_id=event.external_event_id,
                event_type=event.event_type,
                received_at=event.received_at,
                processed=event.processed,
            )
            .on_conflict_do_nothing(index_elements=["external_event_id"])
            .returning(m.PaymentEventModel.id)
        )
        return (await self._s.execute(stmt)).scalar_one_or_none() is not None
