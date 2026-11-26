"""Initial schema: users, consents, pets, pauses, meal logs, points, usage, billing.

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ts(name: str, *, nullable: bool = False) -> sa.Column[Any]:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def _user_fk() -> sa.Column[Any]:
    return sa.Column(
        "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("analytics_opt_out", sa.Boolean(), nullable=False),
        _ts("adult_confirmed_at"),
        _ts("created_at"),
        _ts("deletion_requested_at", nullable=True),
    )
    op.create_table(
        "consents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        _ts("created_at"),
    )
    op.create_index("ix_consents_user_type_created", "consents", ["user_id", "type", "created_at"])
    op.create_table(
        "pets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("color", sa.String(20), nullable=False),
        sa.Column("lives", sa.Integer(), nullable=False),
        sa.Column("streak_days", sa.Integer(), nullable=False),
        sa.Column("last_log_day", sa.Date()),
        sa.Column("settled_on", sa.Date(), nullable=False),
        _ts("rest_until", nullable=True),
        sa.Column("last_seen_lives", sa.Integer()),
        _ts("created_at"),
        sa.CheckConstraint("lives >= 0", name="ck_pets_lives_non_negative"),
        sa.CheckConstraint("streak_days >= 0", name="ck_pets_streak_non_negative"),
    )
    op.create_table(
        "pauses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        _ts("started_at"),
        _ts("ends_at"),
    )
    op.create_index("ix_pauses_user", "pauses", ["user_id", "started_at"])
    op.create_table(
        "meal_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        _ts("logged_at"),
        sa.Column("local_day", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(16), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("food_groups", sa.JSON(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("plate_share", sa.JSON(), nullable=False),
        sa.Column("new_foods", sa.JSON(), nullable=False),
        _ts("deleted_at", nullable=True),
    )
    op.create_index("ix_meal_logs_user_logged", "meal_logs", ["user_id", "logged_at", "id"])
    op.create_table(
        "points_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("local_day", sa.Date(), nullable=False),
        _ts("created_at"),
        sa.CheckConstraint("amount > 0", name="ck_points_events_positive"),
    )
    op.create_index(
        "ix_points_events_user_day", "points_events", ["user_id", "local_day", "reason"]
    )
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _user_fk(),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("platform", sa.String(16), nullable=False),
        _ts("created_at"),
    )
    op.create_table(
        "daily_usage",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("local_day", sa.Date(), primary_key=True),
        sa.Column("analyses", sa.Integer(), nullable=False),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        _ts("current_period_end", nullable=True),
        _ts("created_at"),
    )
    op.create_table(
        "payment_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("external_event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        _ts("received_at"),
        sa.Column("processed", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("payment_events")
    op.drop_table("subscriptions")
    op.drop_table("daily_usage")
    op.drop_table("push_tokens")
    op.drop_index("ix_points_events_user_day", table_name="points_events")
    op.drop_table("points_events")
    op.drop_index("ix_meal_logs_user_logged", table_name="meal_logs")
    op.drop_table("meal_logs")
    op.drop_index("ix_pauses_user", table_name="pauses")
    op.drop_table("pauses")
    op.drop_table("pets")
    op.drop_index("ix_consents_user_type_created", table_name="consents")
    op.drop_table("consents")
    op.drop_table("users")
