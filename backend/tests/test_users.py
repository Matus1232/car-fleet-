import pytest
from sqlalchemy import select

from app import cli
from app.db.session import SessionLocal
from app.models.user import User

NEW_USER = {"email": "jan@example.com", "password": "secret password"}


def test_admin_creates_user_who_can_log_in(admin_client, client):
    resp = admin_client.post("/users", json=NEW_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "jan@example.com"
    assert body["role"] == "driver"  # predvolená rola
    assert "password" not in body
    assert "hashed_password" not in body

    login = client.post(
        "/auth/token", data={"username": NEW_USER["email"], "password": NEW_USER["password"]}
    )
    assert login.status_code == 200


def test_admin_can_create_another_admin(admin_client):
    resp = admin_client.post("/users", json={**NEW_USER, "role": "admin"})
    assert resp.json()["role"] == "admin"


def test_email_is_normalized(admin_client):
    resp = admin_client.post("/users", json={**NEW_USER, "email": "  Jan@Example.COM "})
    assert resp.json()["email"] == "jan@example.com"


@pytest.mark.parametrize("email", ["jan@example.com", "JAN@example.com"])
def test_duplicate_email_returns_409(admin_client, email):
    admin_client.post("/users", json=NEW_USER)
    resp = admin_client.post("/users", json={**NEW_USER, "email": email})
    assert resp.status_code == 409
    assert resp.json()["detail"] == "A user with this email already exists"


@pytest.mark.parametrize(
    "payload",
    [
        {**NEW_USER, "email": "not-an-email"},
        {**NEW_USER, "password": "short"},
        {**NEW_USER, "password": "x" * 129},
        {**NEW_USER, "role": "superadmin"},
        {"email": "jan@example.com"},
    ],
)
def test_create_user_validation_errors(admin_client, payload):
    assert admin_client.post("/users", json=payload).status_code == 422


def test_driver_cannot_create_users(driver_client):
    assert driver_client.post("/users", json=NEW_USER).status_code == 403


def test_anonymous_cannot_create_users(client):
    assert client.post("/users", json=NEW_USER).status_code == 401


def test_cli_creates_admin(monkeypatch, capsys):
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "admin password")
    cli.create_admin("Boss@Example.com")
    assert "boss@example.com" in capsys.readouterr().out
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "boss@example.com"))
    assert user.role == "admin"


def test_cli_rejects_mismatched_passwords(monkeypatch):
    answers = iter(["first password", "second password"])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: next(answers))
    with pytest.raises(SystemExit):
        cli.create_admin("boss@example.com")
