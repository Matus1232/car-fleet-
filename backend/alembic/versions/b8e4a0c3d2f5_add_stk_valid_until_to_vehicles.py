"""add stk_valid_until to vehicles

Revision ID: b8e4a0c3d2f5
Revises: a7d3f9b2c1e4
Create Date: 2026-11-14 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8e4a0c3d2f5"
down_revision: Union[str, None] = "a7d3f9b2c1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # nullable=True: autá, ktoré už v databáze sú, dátum STK nemajú a ostanú s prázdnou hodnotou.
    op.add_column("vehicles", sa.Column("stk_valid_until", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("vehicles", "stk_valid_until")
