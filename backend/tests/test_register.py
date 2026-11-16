import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User

NEW_USER = {"email": "jan@example.com", "password": "secret password"}


def test_anyone_can_register_and_log_in(client):
    resp = client.post("/auth/register", json=NEW_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "jan@example.com"
    assert body["role"] == "driver"
    assert "password" not in body
    assert "hashed_password" not in body

    login = client.post(
        "/auth/token", data={"username": NEW_USER["email"], "password": NEW_USER["password"]}
    )
    assert login.status_code == 200


def test_registration_cannot_create_admin(client):
    # Rolu si človek pri registrácii nevyberá. Aj keď ju pošle, vznikne obyčajný používateľ.
    resp = client.post("/auth/register", json={**NEW_USER, "role": "admin"})
    assert resp.status_code == 201
    assert resp.json()["role"] == "driver"
    with SessionLocal() as db:
        assert db.scalar(select(User.role).where(User.email == NEW_USER["email"])) == "driver"


def test_registered_user_cannot_modify_vehicles(client):
    client.post("/auth/register", json=NEW_USER)
    token = client.post(
        "/auth/token", data={"username": NEW_USER["email"], "password": NEW_USER["password"]}
    ).json()["access_token"]
    resp = client.post(
        "/vehicles",
        json={"brand": "Skoda", "model": "Octavia", "license_plate": "BA123AB"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_register_normalizes_email(client):
    resp = client.post("/auth/register", json={**NEW_USER, "email": "  Jan@Example.COM "})
    assert resp.json()["email"] == "jan@example.com"


@pytest.mark.parametrize("email", ["jan@example.com", "JAN@example.com"])
def test_register_duplicate_email_returns_409(client, email):
    client.post("/auth/register", json=NEW_USER)
    resp = client.post("/auth/register", json={**NEW_USER, "email": email})
    assert resp.status_code == 409
    assert resp.json()["detail"] == "A user with this email already exists"


@pytest.mark.parametrize(
    "payload",
    [
        {**NEW_USER, "email": "not-an-email"},
        {**NEW_USER, "password": "short"},
        {**NEW_USER, "password": "x" * 129},
        {"email": "jan@example.com"},
        {"password": "secret password"},
    ],
)
def test_register_validation_errors(client, payload):
    assert client.post("/auth/register", json=payload).status_code == 422


def test_register_is_rate_limited(client):
    for i in range(settings.register_max_attempts):
        resp = client.post("/auth/register", json={**NEW_USER, "email": f"user{i}@example.com"})
        assert resp.status_code == 201

    resp = client.post("/auth/register", json={**NEW_USER, "email": "one-too-many@example.com"})
    assert resp.status_code == 429
    assert int(resp.headers["Retry-After"]) > 0
    # Odmietnutá registrácia nesmie v databáze nič nechať.
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(User)) == settings.register_max_attempts


def test_invalid_payload_does_not_count_towards_limit(client):
    # Validácia (422) prebehne skôr, než sa pokus započíta, takže preklep nikoho nezablokuje.
    for _ in range(settings.register_max_attempts + 1):
        assert client.post("/auth/register", json={"email": "x"}).status_code == 422
    assert client.post("/auth/register", json=NEW_USER).status_code == 201
