from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token
from app.db.session import SessionLocal
from app.models.user import Role, User
from tests.conftest import PASSWORD

VEHICLE = {"brand": "Skoda", "model": "Octavia", "license_plate": "BA123AB"}


def login(client, email, password):
    # OAuth2 posiela meno a heslo ako formulár (data=), nie ako JSON.
    return client.post("/auth/token", data={"username": email, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# --- Prihlásenie (autentifikácia) ---


def test_login_returns_token_that_works(client, make_user):
    make_user(email="jan@example.com")
    resp = login(client, "jan@example.com", PASSWORD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"

    me = client.get("/auth/me", headers=bearer(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "jan@example.com"
    assert me.json()["role"] == "driver"


def test_login_email_is_case_insensitive(client, make_user):
    make_user(email="jan@example.com")
    assert login(client, "  Jan@Example.COM ", PASSWORD).status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("jan@example.com", "wrong password"),  # zlé heslo
        ("nobody@example.com", PASSWORD),  # neexistujúci email
        ("jan@example.com", PASSWORD.upper()),  # heslo rozlišuje veľké a malé písmená
    ],
)
def test_login_failure_does_not_reveal_which_part_was_wrong(client, make_user, email, password):
    make_user(email="jan@example.com")
    resp = login(client, email, password)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"
    assert resp.headers["WWW-Authenticate"] == "Bearer"


def test_password_is_stored_hashed(make_user):
    user = make_user()
    assert user.hashed_password != PASSWORD
    assert user.hashed_password.startswith("$argon2")


# --- Overenie tokenu ---


def test_me_without_token_returns_401(client):
    assert client.get("/auth/me").status_code == 401


def _token(sub="1", minutes=30, key=None, algorithm=ALGORITHM):
    exp = datetime.now(UTC) + timedelta(minutes=minutes)
    return jwt.encode({"sub": sub, "exp": exp}, key or settings.secret_key, algorithm=algorithm)


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        _token(minutes=-1),  # vypršaný
        _token(key="some-other-secret-key-of-sufficient-length"),  # podpísaný cudzím kľúčom
        _token(sub="abc"),  # nezmyselné ID
        jwt.encode({"sub": "1"}, "x" * 32, algorithm=ALGORITHM),  # bez exp
    ],
)
def test_invalid_token_returns_401(client, make_user, token):
    make_user()  # používateľ s id=1 existuje, takže 401 spôsobí naozaj len zlý token
    assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_unsigned_token_is_rejected(client, make_user):
    # Útok "alg: none": token bez podpisu. Server ho nesmie prijať.
    make_user()
    exp = datetime.now(UTC) + timedelta(minutes=30)
    token = jwt.encode({"sub": "1", "exp": exp}, key=None, algorithm="none")
    assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_tampered_token_is_rejected(client, make_user):
    make_user()
    # Útočník si v payloade prepíše ID na iného používateľa, ale podpis nechá pôvodný.
    header, _payload, signature = create_access_token(1).split(".")
    forged = jwt.utils.base64url_encode(b'{"sub":"2","exp":9999999999}').decode()
    token = f"{header}.{forged}.{signature}"
    assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_token_of_deleted_user_returns_401(client, make_user):
    user = make_user()
    token = create_access_token(user.id)
    with SessionLocal() as db:
        db.delete(db.get(User, user.id))
        db.commit()
    assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_role_change_applies_immediately(client, make_user):
    # Rola nie je v tokene, načítava sa z DB, takže degradovaný admin hneď stratí práva.
    user = make_user(email="boss@example.com", role=Role.ADMIN)
    headers = bearer(create_access_token(user.id))
    assert client.post("/vehicles", json=VEHICLE, headers=headers).status_code == 201

    with SessionLocal() as db:
        db.get(User, user.id).role = Role.DRIVER
        db.commit()
    resp = client.post("/vehicles", json={**VEHICLE, "license_plate": "KE1"}, headers=headers)
    assert resp.status_code == 403


# --- Prístup k vozidlám (autorizácia) ---


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/vehicles"),
        ("get", "/vehicles/1"),
        ("post", "/vehicles"),
        ("patch", "/vehicles/1"),
        ("delete", "/vehicles/1"),
    ],
)
def test_vehicles_require_login(client, method, url):
    kwargs = {"json": VEHICLE} if method in ("post", "patch") else {}
    assert getattr(client, method)(url, **kwargs).status_code == 401


def test_driver_can_read_vehicles(driver_client, make_vehicle):
    created = make_vehicle()
    assert driver_client.get("/vehicles").json()["total"] == 1
    assert driver_client.get(f"/vehicles/{created['id']}").status_code == 200


def test_driver_cannot_modify_vehicles(driver_client, make_vehicle):
    created = make_vehicle()
    url = f"/vehicles/{created['id']}"
    resp = driver_client.post("/vehicles", json={**VEHICLE, "license_plate": "KE1"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin role required"
    assert driver_client.patch(url, json={"model": "Fabia"}).status_code == 403
    assert driver_client.delete(url).status_code == 403
    assert driver_client.get(url).json() == created  # nič sa nezmenilo
