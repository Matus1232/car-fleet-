"""create bookings table

Revision ID: d1a5c8e7f3b6
Revises: b8e4a0c3d2f5
Create Date: 2026-11-16 23:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1a5c8e7f3b6"
down_revision: Union[str, None] = "b8e4a0c3d2f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("hour", sa.SmallInteger(), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        # Keď sa zmaže používateľ, databáza zmaže aj jeho rezervácie.
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # Jeden termín (deň + hodina) smie mať len jednu rezerváciu.
        sa.UniqueConstraint("booking_date", "hour", name="bookings_slot_key"),
        sa.CheckConstraint("hour BETWEEN 8 AND 16", name="bookings_hour_check"),
    )
    op.create_index(op.f("ix_bookings_user_id"), "bookings", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_user_id"), table_name="bookings")
    op.drop_table("bookings")
