"""Notification preferences on users (meal reminder, sleepy notice, weekly summary, quiet hours).

Revision ID: 0002_notification_prefs
Revises: 0001
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_notification_prefs"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BOOLEANS = ("notify_meal_reminder", "notify_sleepy", "notify_weekly_summary")


def upgrade() -> None:
    for name in _BOOLEANS:
        op.add_column(
            "users", sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.true())
        )
    op.add_column(
        "users",
        sa.Column("quiet_hours_start", sa.Time(), nullable=False, server_default="22:00:00"),
    )
    op.add_column(
        "users",
        sa.Column("quiet_hours_end", sa.Time(), nullable=False, server_default="08:00:00"),
    )


def downgrade() -> None:
    op.drop_column("users", "quiet_hours_end")
    op.drop_column("users", "quiet_hours_start")
    for name in reversed(_BOOLEANS):
        op.drop_column("users", name)
