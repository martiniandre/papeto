"""Pet name is nullable: a new pet has no name until the user names it (screen 43).

Existing rows keep their name. Downgrade fills missing names with the old default before
restoring NOT NULL.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREVIOUS_DEFAULT_NAME = "Bolinha"


def upgrade() -> None:
    with op.batch_alter_table("pets") as batch:
        batch.alter_column("name", existing_type=sa.String(20), nullable=True)


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE pets SET name = :name WHERE name IS NULL").bindparams(
            name=_PREVIOUS_DEFAULT_NAME
        )
    )
    with op.batch_alter_table("pets") as batch:
        batch.alter_column("name", existing_type=sa.String(20), nullable=False)
