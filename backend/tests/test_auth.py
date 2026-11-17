from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token
from app.db.session import SessionLocal
from app.models.revoked_token import RevokedToken
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


def _token(sub="1", minutes=30, key=None, jti="test-jti", drop=()):
    """Ručne vyrobený token. Každý prípad nižšie pokazí len jednu vec, ostatné sú v poriadku."""
    exp = datetime.now(UTC) + timedelta(minutes=minutes)
    payload = {"sub": sub, "exp": exp, "jti": jti}
    for claim in drop:
        del payload[claim]
    return jwt.encode(payload, key or settings.secret_key, algorithm=ALGORITHM)


def test_hand_made_token_is_valid(client, make_user):
    # Kontrola testu: bez pokazenia je ručne vyrobený token platný, takže 401 nižšie
    # spôsobí naozaj len tá jedna pokazená vec.
    make_user()
    assert client.get("/auth/me", headers=bearer(_token())).status_code == 200


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        _token(minutes=-1),  # vypršaný
        _token(key="some-other-secret-key-of-sufficient-length"),  # podpísaný cudzím kľúčom
        _token(sub="abc"),  # nezmyselné ID
        _token(drop=["exp"]),  # bez času vypršania
        _token(drop=["jti"]),  # bez ID tokenu: taký by sa nedal odhlásiť
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


# --- httpOnly cookie ---

CSRF = {"X-Requested-With": "fetch"}


def test_login_sets_httponly_cookie(client, make_user):
    make_user(email="jan@example.com")
    resp = login(client, "jan@example.com", PASSWORD)
    cookie = resp.headers["set-cookie"].lower()
    assert cookie.startswith("access_token=")
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert f"max-age={settings.access_token_expire_minutes * 60}" in cookie


def test_cookie_is_secure_when_configured(client, make_user, monkeypatch):
    # Na Railway (HTTPS) je cookie_secure zapnuté: prehliadač ju cez HTTP nepošle.
    monkeypatch.setattr(settings, "cookie_secure", True)
    make_user(email="jan@example.com")
    resp = login(client, "jan@example.com", PASSWORD)
    assert "secure" in resp.headers["set-cookie"].lower()


def test_cookie_alone_signs_user_in(client, make_user):
    # Frontend neposiela hlavičku Authorization, prehliadač pripojí cookie sám.
    make_user(email="jan@example.com")
    login(client, "jan@example.com", PASSWORD)  # TestClient si cookie zapamätá
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "jan@example.com"


def test_cookie_write_without_csrf_header_is_rejected(client, make_user):
    # Cudzia stránka vie prinútiť prehliadač poslať POST s našou cookie, ale nevie pridať hlavičku.
    make_user(email="boss@example.com", role=Role.ADMIN)
    login(client, "boss@example.com", PASSWORD)

    resp = client.post("/vehicles", json=VEHICLE)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Missing X-Requested-With header"
    assert client.post("/vehicles", json=VEHICLE, headers=CSRF).status_code == 201


def test_bearer_token_does_not_need_csrf_header(client, make_user):
    # Hlavičku Authorization prehliadač nikdy nepridá sám, takže tu CSRF hrozba nie je.
    user = make_user(email="boss@example.com", role=Role.ADMIN)
    headers = bearer(create_access_token(user.id))
    assert client.post("/vehicles", json=VEHICLE, headers=headers).status_code == 201


# --- Odhlásenie ---


def test_logout_revokes_token_and_clears_cookie(client, make_user):
    make_user(email="jan@example.com")
    token = login(client, "jan@example.com", PASSWORD).json()["access_token"]

    resp = client.post("/auth/logout", headers=CSRF)
    assert resp.status_code == 204
    # Max-Age=0 = prehliadač má cookie hneď zmazať.
    assert 'access_token=""' in resp.headers["set-cookie"]
    assert "max-age=0" in resp.headers["set-cookie"].lower()

    # Aj keby si niekto token predtým skopíroval, už neplatí, hoci ešte nevypršal.
    assert client.get("/auth/me", headers=bearer(token)).status_code == 401


def test_logout_revokes_only_that_token(client, make_user):
    # Odhlásenie na jednom zariadení neodhlási ostatné (každé má vlastný token s iným jti).
    user = make_user()
    phone, laptop = create_access_token(user.id), create_access_token(user.id)
    assert client.post("/auth/logout", headers=bearer(phone)).status_code == 204
    assert client.get("/auth/me", headers=bearer(phone)).status_code == 401
    assert client.get("/auth/me", headers=bearer(laptop)).status_code == 200


def test_logout_requires_login(client):
    assert client.post("/auth/logout", headers=CSRF).status_code == 401


def test_logout_forgets_expired_revoked_tokens(client, make_user):
    # Zoznam odhlásených tokenov nerastie donekonečna: tie, čo by už aj tak neplatili, sa zmažú.
    user = make_user()
    with SessionLocal() as db:
        old = datetime.now(UTC) - timedelta(minutes=1)
        db.add(RevokedToken(jti="old-token", expires_at=old))
        db.commit()
    client.post("/auth/logout", headers=bearer(create_access_token(user.id)))
    with SessionLocal() as db:
        assert db.get(RevokedToken, "old-token") is None
        assert db.scalar(select(func.count()).select_from(RevokedToken)) == 1


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


@pytest.mark.parametrize("url", ["/vehicles", "/vehicles/1", "/vehicles/stats"])
def test_driver_cannot_read_vehicles(driver_client, make_vehicle, url):
    # Registrácia je verejná, takže bežný účet nesmie vidieť ani zoznam áut.
    make_vehicle()
    resp = driver_client.get(url)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin role required"


def test_driver_cannot_modify_vehicles(admin_client, driver_client, make_vehicle):
    created = make_vehicle()
    url = f"/vehicles/{created['id']}"
    resp = driver_client.post("/vehicles", json={**VEHICLE, "license_plate": "KE1"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin role required"
    assert driver_client.patch(url, json={"model": "Fabia"}).status_code == 403
    assert driver_client.delete(url).status_code == 403
    assert admin_client.get(url).json() == created  # nič sa nezmenilo
