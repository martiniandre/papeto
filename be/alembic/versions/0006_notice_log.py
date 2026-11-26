"""Notice log: what push notices were sent, so none is sent twice.

Revision ID: 0006_notice_log
Revises: 0005_notification_prefs
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_notice_log"
down_revision: str | None = "0005_notification_prefs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notice_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("episode_day", sa.Date(), nullable=False),
        sa.Column("local_day", sa.Date(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "kind", "episode_day", name="uq_notice_log_episode"),
    )
    op.create_index("ix_notice_log_user_day", "notice_log", ["user_id", "local_day"])


def downgrade() -> None:
    op.drop_index("ix_notice_log_user_day", table_name="notice_log")
    op.drop_table("notice_log")
