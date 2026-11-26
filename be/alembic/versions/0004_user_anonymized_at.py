"""Mark accounts whose personal data was erased after the 30-day deletion grace period.

Revision ID: 0004_user_anonymized_at
Revises: 0003_notice_log
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_user_anonymized_at"
down_revision: str | None = "0003_notice_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "anonymized_at")
