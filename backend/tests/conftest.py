import os
from pathlib import Path

import pytest

# Testy mažú dáta, preto bežia len nad databázou zadanou explicitne cez TEST_DATABASE_URL
# (nikdy nad DATABASE_URL z .env, aby sa nevymazala vývojová databáza).
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.exit("Nastav TEST_DATABASE_URL na prázdnu testovaciu databázu.", returncode=2)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "development"

from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _migrated_database():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE vehicles RESTART IDENTITY"))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_vehicle(client):
    def _make(brand="Skoda", model="Octavia", license_plate="BA123AB"):
        resp = client.post(
            "/vehicles", json={"brand": brand, "model": model, "license_plate": license_plate}
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make
