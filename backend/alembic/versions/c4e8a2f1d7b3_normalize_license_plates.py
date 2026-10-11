"""normalize existing license plates (uppercase, no spaces or hyphens)

Revision ID: c4e8a2f1d7b3
Revises: 9b1d4c7e5a10
Create Date: 2026-10-12 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8a2f1d7b3"
down_revision: Union[str, None] = "9b1d4c7e5a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# To isté, čo robí normalize_license_plate() v app/schemas/vehicle.py, len v SQL.
NORMALIZED = "upper(regexp_replace(license_plate, '[[:space:]-]', '', 'g'))"


def upgrade() -> None:
    conn = op.get_bind()

    # Ak by po normalizácii vznikli dve rovnaké ŠPZ (napr. 'BA-123AB' a 'BA123AB'),
    # UPDATE by spadol na unique constrainte. Radšej skončíme zrozumiteľnou chybou
    # a duplicity treba vyriešiť ručne.
    duplicates = conn.execute(
        sa.text(
            f"SELECT {NORMALIZED} FROM vehicles WHERE {NORMALIZED} <> '' "
            "GROUP BY 1 HAVING count(*) > 1"
        )
    ).scalars().all()
    if duplicates:
        raise RuntimeError(
            "After normalization these license plates would be duplicate, "
            "resolve them manually first: " + ", ".join(duplicates)
        )

    # Riadky, z ktorých by ostal prázdny reťazec (napr. '---'), necháme tak.
    conn.execute(
        sa.text(
            f"UPDATE vehicles SET license_plate = {NORMALIZED} "
            f"WHERE {NORMALIZED} <> '' AND license_plate <> {NORMALIZED}"
        )
    )


def downgrade() -> None:
    # Pôvodný zápis (medzery, pomlčky, malé písmená) sa nedá obnoviť; nie je to ani potrebné.
    pass
