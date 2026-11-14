"""create service_records table

Revision ID: a7d3f9b2c1e4
Revises: e6aa44cf5412
Create Date: 2026-11-14 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7d3f9b2c1e4"
down_revision: Union[str, None] = "e6aa44cf5412"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("cost", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        # Keď sa zmaže auto, databáza zmaže aj jeho servisné záznamy.
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.CheckConstraint("cost >= 0", name="service_records_cost_check"),
    )
    op.create_index(
        op.f("ix_service_records_vehicle_id"), "service_records", ["vehicle_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_service_records_vehicle_id"), table_name="service_records")
    op.drop_table("service_records")
