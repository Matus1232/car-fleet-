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
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"

from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from alembic import command  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import Role, User  # noqa: E402

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
        conn.execute(text("TRUNCATE vehicles, users RESTART IDENTITY"))


PASSWORD = "correct horse battery"


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.fixture
def make_user():
    """Vloží používateľa rovno do DB (bez API), aby testy nezáviseli od POST /users."""

    def _make(email="driver@example.com", password=PASSWORD, role=Role.DRIVER) -> User:
        with SessionLocal() as db:
            user = User(email=email, hashed_password=hash_password(password), role=role)
            db.add(user)
            db.commit()
            return user

    return _make


@pytest.fixture
def client():
    """Neprihlásený klient, bez tokenu."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_client(make_user):
    admin = make_user(email="admin@example.com", role=Role.ADMIN)
    with TestClient(app, headers=auth_headers(admin)) as c:
        yield c


@pytest.fixture
def driver_client(make_user):
    driver = make_user(email="driver@example.com", role=Role.DRIVER)
    with TestClient(app, headers=auth_headers(driver)) as c:
        yield c


@pytest.fixture
def make_vehicle(admin_client):
    def _make(brand="Skoda", model="Octavia", license_plate="BA123AB"):
        resp = admin_client.post(
            "/vehicles", json={"brand": brand, "model": model, "license_plate": license_plate}
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make
