import pytest

from app.core.config import Settings

SECRET = "x" * 32


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # Tak ju dáva Railway: bez ovládača by SQLAlchemy hľadal psycopg2, ktorý nemáme.
        ("postgresql://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        # Adresa s ovládačom ostane, ako je.
        ("postgresql+psycopg://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ],
)
def test_database_url_uses_psycopg_driver(given, expected):
    assert Settings(database_url=given, secret_key=SECRET).database_url == expected
