"""make vehicles.created_at timezone aware

Revision ID: 9b1d4c7e5a10
Revises: 2f0c2c439792
Create Date: 2026-10-11 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b1d4c7e5a10"
down_revision: Union[str, None] = "2f0c2c439792"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pôvodné hodnoty boli naive UTC (now() na serveri s UTC časom)
    op.alter_column(
        "vehicles",
        "created_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "vehicles",
        "created_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
