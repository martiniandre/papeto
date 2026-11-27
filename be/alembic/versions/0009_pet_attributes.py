"""Pet attributes (spent attribute points) and the last level returned to the client.

The level is not stored: it is computed from the points total. Existing pets start with every
attribute at 0 and `last_seen_level` NULL (no `level_up` event until the server first returns one).

Revision ID: 0009_pet_attributes
Revises: 0008_meal_vision_metadata
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_pet_attributes"
down_revision: str | None = "0008_meal_vision_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ATTRIBUTES = ("strength", "speed", "skill", "endurance", "intelligence")


def upgrade() -> None:
    with op.batch_alter_table("pets") as batch:
        for name in _ATTRIBUTES:
            batch.add_column(
                sa.Column(f"attr_{name}", sa.Integer(), nullable=False, server_default="0")
            )
        batch.add_column(sa.Column("last_seen_level", sa.Integer(), nullable=True))
        batch.create_check_constraint(
            "ck_pets_attributes_non_negative",
            " AND ".join(f"attr_{name} >= 0" for name in _ATTRIBUTES),
        )


def downgrade() -> None:
    with op.batch_alter_table("pets") as batch:
        batch.drop_constraint("ck_pets_attributes_non_negative", type_="check")
        batch.drop_column("last_seen_level")
        for name in reversed(_ATTRIBUTES):
            batch.drop_column(f"attr_{name}")
