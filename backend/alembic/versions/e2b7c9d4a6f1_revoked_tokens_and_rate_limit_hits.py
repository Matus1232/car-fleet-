"""create revoked_tokens and rate_limit_hits tables

Revision ID: e2b7c9d4a6f1
Revises: d1a5c8e7f3b6
Create Date: 2026-11-17 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2b7c9d4a6f1"
down_revision: Union[str, None] = "d1a5c8e7f3b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Odhlásené tokeny, ktoré ešte nevypršali.
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index(
        op.f("ix_revoked_tokens_expires_at"), "revoked_tokens", ["expires_at"], unique=False
    )

    # Pokusy o prihlásenie a registráciu pre rate limiter.
    op.create_table(
        "rate_limit_hits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rate_limit_hits_lookup", "rate_limit_hits", ["scope", "key", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_rate_limit_hits_lookup", table_name="rate_limit_hits")
    op.drop_table("rate_limit_hits")
    op.drop_index(op.f("ix_revoked_tokens_expires_at"), table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
