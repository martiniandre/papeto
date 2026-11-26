"""SQLAlchemy 2.0 models. All instants are `timestamptz` (UTC); local days are stored as `date`.

There is deliberately no column for calories, macros, weight or scores. Photos are never stored.
Table names are plural because `user` is a reserved word in Postgres.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
    Uuid,
    true,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _ts() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True))


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(64))
    analytics_opt_out: Mapped[bool] = mapped_column(Boolean, default=False)
    adult_confirmed_at: Mapped[datetime] = _ts()
    created_at: Mapped[datetime] = _ts()
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notify_meal_reminder: Mapped[bool] = mapped_column(Boolean, server_default=true())
    notify_sleepy: Mapped[bool] = mapped_column(Boolean, server_default=true())
    notify_weekly_summary: Mapped[bool] = mapped_column(Boolean, server_default=true())
    quiet_hours_start: Mapped[time] = mapped_column(Time, server_default="22:00:00")
    quiet_hours_end: Mapped[time] = mapped_column(Time, server_default="08:00:00")


class ConsentModel(Base):
    """Append-only consent history. The latest row per (user, type) is the current state."""

    __tablename__ = "consents"
    __table_args__ = (Index("ix_consents_user_type_created", "user_id", "type", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(32))
    accepted: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = _ts()


class PetModel(Base):
    __tablename__ = "pets"
    __table_args__ = (
        CheckConstraint("lives >= 0", name="ck_pets_lives_non_negative"),
        CheckConstraint("streak_days >= 0", name="ck_pets_streak_non_negative"),
        CheckConstraint(
            "attr_strength >= 0 AND attr_speed >= 0 AND attr_skill >= 0"
            " AND attr_endurance >= 0 AND attr_intelligence >= 0",
            name="ck_pets_attributes_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str | None] = mapped_column(String(20))  # None until the user names it
    color: Mapped[str] = mapped_column(String(20))
    lives: Mapped[int] = mapped_column(Integer)
    streak_days: Mapped[int] = mapped_column(Integer)
    last_log_day: Mapped[date | None] = mapped_column(Date)
    settled_on: Mapped[date] = mapped_column(Date)
    rest_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_lives: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _ts()
    # Spent attribute points (display only in the MVP). The level itself is computed from points.
    attr_strength: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    attr_speed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    attr_skill: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    attr_endurance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    attr_intelligence: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_seen_level: Mapped[int | None] = mapped_column(Integer)


class PauseModel(Base):
    """Pause history: the domain turns `[started_at, ends_at)` into `PauseWindow`s."""

    __tablename__ = "pauses"
    __table_args__ = (Index("ix_pauses_user", "user_id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = _ts()
    ends_at: Mapped[datetime] = _ts()


class MealLogModel(Base):
    __tablename__ = "meal_logs"
    __table_args__ = (Index("ix_meal_logs_user_logged", "user_id", "logged_at", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    logged_at: Mapped[datetime] = _ts()
    local_day: Mapped[date] = mapped_column(Date)
    meal_type: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(String(500))
    items: Mapped[list[str]] = mapped_column(JSON)
    food_groups: Mapped[list[str]] = mapped_column(JSON)
    item_count: Mapped[int] = mapped_column(Integer)
    colors: Mapped[list[str]] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    plate_share: Mapped[dict[str, float]] = mapped_column(JSON)
    new_foods: Mapped[list[str]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(16), default="photo")  # photo | manual
    vision_provider: Mapped[str | None] = mapped_column(String(32))
    model_version: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PointsEventModel(Base):
    """Append-only and always positive. Repositories expose no update or delete."""

    __tablename__ = "points_events"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_points_events_positive"),
        Index("ix_points_events_user_day", "user_id", "local_day", "reason"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(Integer)
    local_day: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = _ts()


class PasswordResetModel(Base):
    """Single-use password reset tokens. Only the SHA-256 hash of the token is stored."""

    __tablename__ = "password_resets"
    __table_args__ = (Index("ix_password_resets_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = _ts()
    expires_at: Mapped[datetime] = _ts()
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PushTokenModel(Base):
    __tablename__ = "push_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(255), unique=True)
    platform: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = _ts()


class NoticeLogModel(Base):
    """Every push notice that was decided, so none is sent twice and the daily cap is enforced."""

    __tablename__ = "notice_log"
    __table_args__ = (
        UniqueConstraint("user_id", "kind", "episode_day", name="uq_notice_log_episode"),
        Index("ix_notice_log_user_day", "user_id", "local_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    episode_day: Mapped[date] = mapped_column(Date)
    local_day: Mapped[date] = mapped_column(Date)
    sent_at: Mapped[datetime] = _ts()


class DailyUsageModel(Base):
    """Logs per user and local day.

    `analyses` counts successful photo analyses (the AI limit; failed ones are never counted).
    `manual_logs` counts meals entered by hand (RF-95): they make the day a logged day but never
    consume the AI limit.
    """

    __tablename__ = "daily_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    local_day: Mapped[date] = mapped_column(Date, primary_key=True)
    analyses: Mapped[int] = mapped_column(Integer, default=0)
    manual_logs: Mapped[int] = mapped_column(Integer, default=0)


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _ts()


class PaymentEventModel(Base):
    __tablename__ = "payment_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    external_event_id: Mapped[str] = mapped_column(String(255), unique=True)
    event_type: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = _ts()
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
