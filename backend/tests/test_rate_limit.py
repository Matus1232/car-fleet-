from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limit import RateLimiter, RateLimitExceeded
from app.main import app
from tests.conftest import PASSWORD


class FakeClock:
    """Hodiny, ktoré sa posúvajú len keď povieme, takže test nemusí naozaj čakať."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def limiter(clock):
    return RateLimiter(max_attempts=3, window_seconds=60, clock=clock)


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


def test_concurrent_requests_cannot_exceed_limit(clock):
    limiter = RateLimiter(max_attempts=5, window_seconds=60, clock=clock)

    def try_once(_):
        try:
            limiter.acquire("ip")
            return True
        except RateLimitExceeded:
            return False

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(try_once, range(100)))
    assert results.count(True) == 5


def test_old_keys_are_forgotten(limiter, clock):
    for i in range(100):
        limiter.acquire(f"10.0.0.{i}")
    assert limiter.tracked_keys() == 100
    clock.advance(61)
    limiter.acquire("new-ip")  # spustí upratovanie
    assert limiter.tracked_keys() == 1


# --- Endpoint /auth/token ---


def login(client, password, email="jan@example.com"):
    return client.post("/auth/token", data={"username": email, "password": password})


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
