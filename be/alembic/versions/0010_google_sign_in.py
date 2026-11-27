"""Google sign-in: how the account was created, the linked Google subject, and adult confirmation
that can come after sign-up (ADR 013).

- `users.auth_provider`: "email" (default for every existing row) or "google".
- `users.google_subject`: the Google `sub` claim from a verified ID token, unique, nullable.
- `users.adult_confirmed_at` becomes nullable: a Google account exists before the 18+ checkbox.

Downgrade refuses to run while any account has no adult confirmation, because filling the column
would invent a confirmation the user never gave. Confirm or remove those accounts first.

Revision ID: 0010_google_sign_in
Revises: 0009_pet_attributes
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_google_sign_in"
down_revision: str | None = "0009_pet_attributes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column("auth_provider", sa.String(16), nullable=False, server_default="email")
        )
        batch.add_column(sa.Column("google_subject", sa.String(255), nullable=True))
        batch.create_unique_constraint("uq_users_google_subject", ["google_subject"])
        batch.alter_column(
            "adult_confirmed_at", existing_type=sa.DateTime(timezone=True), nullable=True
        )


def downgrade() -> None:
    unconfirmed = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM users WHERE adult_confirmed_at IS NULL"))
        .scalar_one()
    )
    if unconfirmed:
        raise RuntimeError(
            f"{unconfirmed} account(s) have no adult confirmation; "
            "refusing to invent one. Confirm or remove them before downgrading."
        )
    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "adult_confirmed_at", existing_type=sa.DateTime(timezone=True), nullable=False
        )
        batch.drop_constraint("uq_users_google_subject", type_="unique")
        batch.drop_column("google_subject")
        batch.drop_column("auth_provider")
