"""Manual meal entry (RF-95): meal source and a manual log counter per local day.

`meal_logs.source` is `photo` or `manual` (existing rows are photo logs).
`daily_usage.manual_logs` makes a day a logged day without consuming the AI photo limit.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("meal_logs") as batch:
        batch.add_column(sa.Column("source", sa.String(16), nullable=False, server_default="photo"))
    with op.batch_alter_table("daily_usage") as batch:
        batch.add_column(sa.Column("manual_logs", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    # Keep manual-only days as logged days (the old schema only knew `analyses`), so a downgrade
    # never turns a logged day into a missed one. Past days' photo counts no longer matter.
    op.execute("UPDATE daily_usage SET analyses = 1 WHERE analyses = 0 AND manual_logs > 0")
    with op.batch_alter_table("daily_usage") as batch:
        batch.drop_column("manual_logs")
    with op.batch_alter_table("meal_logs") as batch:
        batch.drop_column("source")
