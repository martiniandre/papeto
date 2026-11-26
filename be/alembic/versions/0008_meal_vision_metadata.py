"""Record which vision provider, model and prompt analyzed each photo meal.

All three columns are nullable: manual meals (RF-95) and rows from before this revision have none.
They hold identifiers only (for example "fake" / "fake-1" / "meal-v1"), never image data.

Revision ID: 0008_meal_vision_metadata
Revises: 0007_user_anonymized_at
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_meal_vision_metadata"
down_revision: str | None = "0007_user_anonymized_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("meal_logs") as batch:
        batch.add_column(sa.Column("vision_provider", sa.String(32), nullable=True))
        batch.add_column(sa.Column("model_version", sa.String(100), nullable=True))
        batch.add_column(sa.Column("prompt_version", sa.String(32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("meal_logs") as batch:
        batch.drop_column("prompt_version")
        batch.drop_column("model_version")
        batch.drop_column("vision_provider")
