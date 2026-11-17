from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.rate_limit import RateLimiter, RateLimitExceeded
from app.db.session import SessionLocal
from app.main import app
from app.models.rate_limit_hit import RateLimitHit
from tests.conftest import PASSWORD


class FakeClock:
    """Hodiny, ktoré sa posúvajú len keď povieme, takže test nemusí naozaj čakať."""

    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def limiter(clock):
    return RateLimiter("test", max_attempts=3, window_seconds=60, clock=clock)


def stored_hits() -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(RateLimitHit))


# --- Samotný RateLimiter ---


def test_blocks_after_max_attempts(limiter):
    for _ in range(3):
        limiter.acquire("1.2.3.4")
    with pytest.raises(RateLimitExceeded):
        limiter.acquire("1.2.3.4")


def test_retry_after_says_when_oldest_attempt_expires(limiter, clock):
    limiter.acquire("ip")  # t = 0
    clock.advance(20)
    limiter.acquire("ip")  # t = 20
    limiter.acquire("ip")  # t = 20
    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.acquire("ip")
    assert exc_info.value.retry_after == 40  # prvý pokus vypadne z 60 s okna v čase 60


def test_window_slides(limiter, clock):
    for _ in range(3):
        limiter.acquire("ip")
    clock.advance(59)
    with pytest.raises(RateLimitExceeded):
        limiter.acquire("ip")
    clock.advance(1)  # presne 60 s od prvých pokusov, vypadli z okna
    limiter.acquire("ip")


def test_released_attempt_does_not_count(limiter):
    for _ in range(10):
        limiter.release("ip", limiter.acquire("ip"))
    limiter.acquire("ip")  # stále voľno, nič sa nenapočítalo


def test_keys_are_independent(limiter):
    for _ in range(3):
        limiter.acquire("attacker")
    limiter.acquire("someone-else")


def test_scopes_are_independent(clock):
    # Prihlásenie a registrácia majú jednu tabuľku, ale počítadlá sa nesmú miešať.
    login = RateLimiter("login", max_attempts=1, window_seconds=60, clock=clock)
    register = RateLimiter("register", max_attempts=1, window_seconds=60, clock=clock)
    login.acquire("ip")
    register.acquire("ip")
    with pytest.raises(RateLimitExceeded):
        login.acquire("ip")


def test_attempts_survive_new_limiter_instance(limiter, clock):
    # Pokusy sú v databáze: nový objekt (ako po reštarte aplikácie alebo v inom procese)
    # o nich vie a limit platí ďalej.
    for _ in range(3):
        limiter.acquire("ip")
    after_restart = RateLimiter("test", max_attempts=3, window_seconds=60, clock=clock)
    with pytest.raises(RateLimitExceeded):
        after_restart.acquire("ip")


def test_concurrent_requests_cannot_exceed_limit(clock):
    limiter = RateLimiter("test", max_attempts=5, window_seconds=60, clock=clock)

    def try_once(_):
        try:
            limiter.acquire("ip")
            return True
        except RateLimitExceeded:
            return False

    # Menej vlákien než spojení v pooli SQLAlchemy (5 + 10), aby na seba nečakali zbytočne dlho.
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(try_once, range(40)))
    assert results.count(True) == 5


def test_old_attempts_are_deleted(limiter, clock):
    for i in range(20):
        limiter.acquire(f"10.0.0.{i}")
    assert stored_hits() == 20
    clock.advance(61)
    limiter.acquire("new-ip")  # spustí upratovanie
    assert stored_hits() == 1


# --- Endpoint /auth/token ---


def login(client, password, email="jan@example.com", headers=None):
    return client.post(
        "/auth/token", data={"username": email, "password": password}, headers=headers
    )


def test_too_many_failed_logins_return_429(client, make_user):
    make_user(email="jan@example.com")
    for _ in range(settings.login_max_attempts):
        assert login(client, "wrong password").status_code == 401

    resp = login(client, PASSWORD)  # aj správne heslo je teraz odmietnuté
    assert resp.status_code == 429
    assert resp.json()["detail"] == "Too many failed login attempts, try again later"
    assert int(resp.headers["Retry-After"]) > 0


def test_successful_logins_are_not_limited(client, make_user):
    make_user(email="jan@example.com")
    for _ in range(settings.login_max_attempts + 5):
        assert login(client, PASSWORD).status_code == 200


def test_limit_is_per_ip(client, make_user):
    make_user(email="jan@example.com")
    for _ in range(settings.login_max_attempts):
        login(client, "wrong password")
    assert login(client, PASSWORD).status_code == 429

    with TestClient(app, client=("10.0.0.2", 50000)) as other:
        assert login(other, PASSWORD).status_code == 200


def test_ip_header_is_ignored_unless_configured(client, make_user):
    # Bez nastavenia by si útočník každým pokusom vymyslel novú IP a limit by obišiel.
    make_user(email="jan@example.com")
    for i in range(settings.login_max_attempts):
        login(client, "wrong password", headers={"X-Real-IP": f"6.6.6.{i}"})
    assert login(client, PASSWORD, headers={"X-Real-IP": "7.7.7.7"}).status_code == 429


def test_configured_ip_header_identifies_client(client, make_user, monkeypatch):
    # Za proxy (Railway) prichádzajú všetci z jednej IP, skutočnú posiela proxy v hlavičke.
    monkeypatch.setattr(settings, "client_ip_header", "X-Real-IP")
    make_user(email="jan@example.com")
    for _ in range(settings.login_max_attempts):
        login(client, "wrong password", headers={"X-Real-IP": "1.1.1.1"})
    assert login(client, PASSWORD, headers={"X-Real-IP": "1.1.1.1"}).status_code == 429
    assert login(client, PASSWORD, headers={"X-Real-IP": "2.2.2.2"}).status_code == 200
