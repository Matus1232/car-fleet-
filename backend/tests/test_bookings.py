from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api import bookings
from app.api.bookings import BOOKING_HORIZON_DAYS, BUSINESS_TZ, MAX_RANGE_DAYS
from app.main import app
from tests.conftest import auth_headers


def weekday_in(days: int) -> date:
    """Najbližší pracovný deň, ktorý je aspoň o `days` dní. Testy tak prejdú v ktorýkoľvek deň."""
    day = datetime.now(BUSINESS_TZ).date() + timedelta(days=days)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def slot(days: int = 7, hour: int = 10, **extra) -> dict:
    return {"booking_date": weekday_in(days).isoformat(), "hour": hour, **extra}


def list_range(client, start: date, end: date):
    return client.get("/bookings", params={"start": start.isoformat(), "end": end.isoformat()})


@pytest.fixture
def other_client(make_user):
    """Druhý bežný používateľ, aby sa dalo overiť, čo vidí a smie niekto cudzí."""
    other = make_user(email="other@example.com")
    with TestClient(app, headers=auth_headers(other)) as c:
        yield c


# --- Vytvorenie rezervácie ---


def test_create_booking(driver_client):
    resp = driver_client.post("/bookings", json=slot(note="  Octavia, výmena oleja  "))
    assert resp.status_code == 201
    body = resp.json()
    assert body == {
        "id": 1,
        "booking_date": weekday_in(7).isoformat(),
        "hour": 10,
        "mine": True,
        "user_email": "driver@example.com",
        "note": "Octavia, výmena oleja",  # medzery okolo sú orezané
    }


@pytest.mark.parametrize("note", [None, "", "   "])
def test_note_is_optional(driver_client, note):
    resp = driver_client.post("/bookings", json=slot(note=note))
    assert resp.status_code == 201
    assert resp.json()["note"] is None


def test_same_slot_cannot_be_booked_twice(driver_client, other_client):
    assert driver_client.post("/bookings", json=slot()).status_code == 201
    resp = other_client.post("/bookings", json=slot())
    assert resp.status_code == 409
    assert resp.json()["detail"] == "This slot is already booked"
    # Iná hodina v ten istý deň aj tá istá hodina v iný deň sú voľné.
    assert other_client.post("/bookings", json=slot(hour=11)).status_code == 201
    assert other_client.post("/bookings", json=slot(days=14)).status_code == 201


@pytest.mark.parametrize("hour", [8, 16])
def test_first_and_last_hour_are_bookable(driver_client, hour):
    assert driver_client.post("/bookings", json=slot(hour=hour)).status_code == 201


@pytest.mark.parametrize(
    "payload",
    [
        slot(hour=7),  # pred otvorením
        slot(hour=17),  # po zatvorení
        slot(hour="abc"),
        slot(note="x" * 201),
        {"hour": 10},
        {"booking_date": weekday_in(7).isoformat()},
        {"booking_date": "23.11.2026", "hour": 10},
    ],
)
def test_create_validation_errors(driver_client, payload):
    assert driver_client.post("/bookings", json=payload).status_code == 422


def test_weekend_cannot_be_booked(driver_client):
    saturday = weekday_in(7)
    while saturday.weekday() != 5:
        saturday += timedelta(days=1)
    for day in (saturday, saturday + timedelta(days=1)):
        resp = driver_client.post("/bookings", json={"booking_date": day.isoformat(), "hour": 10})
        assert resp.status_code == 422
        assert resp.json()["detail"] == "Bookings are possible only from Monday to Friday"


def test_past_day_cannot_be_booked(driver_client, monkeypatch):
    # Streda 18. 11. 2026, 10:30 slovenského času.
    monkeypatch.setattr(
        bookings, "_now", lambda: datetime(2026, 11, 18, 10, 30, tzinfo=BUSINESS_TZ)
    )
    resp = driver_client.post("/bookings", json={"booking_date": "2026-11-17", "hour": 10})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "This slot is already in the past"


def test_todays_passed_hours_cannot_be_booked(driver_client, monkeypatch):
    monkeypatch.setattr(
        bookings, "_now", lambda: datetime(2026, 11, 18, 10, 30, tzinfo=BUSINESS_TZ)
    )
    today = "2026-11-18"
    # 9:00 už bolo, 10:00 práve beží, 11:00 je prvý termín, ktorý sa ešte dá stihnúť.
    assert (
        driver_client.post("/bookings", json={"booking_date": today, "hour": 9}).status_code == 422
    )
    assert (
        driver_client.post("/bookings", json={"booking_date": today, "hour": 10}).status_code == 422
    )
    assert (
        driver_client.post("/bookings", json={"booking_date": today, "hour": 11}).status_code == 201
    )


def test_booking_too_far_ahead_is_rejected(driver_client, monkeypatch):
    monkeypatch.setattr(
        bookings, "_now", lambda: datetime(2026, 11, 18, 10, 30, tzinfo=BUSINESS_TZ)
    )
    last_day = date(2026, 11, 18) + timedelta(days=BOOKING_HORIZON_DAYS)
    # Posledný pracovný deň, ktorý sa ešte zmestí, a prvý pracovný deň, ktorý je už priďaleko.
    allowed = last_day
    while allowed.weekday() >= 5:
        allowed -= timedelta(days=1)
    too_far = last_day + timedelta(days=1)
    while too_far.weekday() >= 5:
        too_far += timedelta(days=1)

    ok = driver_client.post("/bookings", json={"booking_date": allowed.isoformat(), "hour": 10})
    assert ok.status_code == 201
    resp = driver_client.post("/bookings", json={"booking_date": too_far.isoformat(), "hour": 10})
    assert resp.status_code == 422
    assert "days ahead" in resp.json()["detail"]


# --- Zoznam rezervácií ---


def test_owner_and_admin_see_details_others_only_that_slot_is_taken(
    driver_client, other_client, admin_client
):
    day = weekday_in(7)
    created = driver_client.post("/bookings", json=slot(note="Fabia, brzdy")).json()

    mine = list_range(driver_client, day, day).json()
    assert mine == [created]

    # Cudzí človek vidí, že termín je obsadený, ale nie kým a prečo.
    foreign = list_range(other_client, day, day).json()
    assert foreign == [{**created, "mine": False, "user_email": None, "note": None}]

    # Admin vidí všetko, len rezervácia nie je jeho.
    as_admin = list_range(admin_client, day, day).json()
    assert as_admin == [{**created, "mine": False}]


def test_list_returns_only_range_ordered_by_day_and_hour(driver_client):
    first, second = weekday_in(7), weekday_in(14)
    driver_client.post("/bookings", json={"booking_date": second.isoformat(), "hour": 9})
    driver_client.post("/bookings", json={"booking_date": first.isoformat(), "hour": 15})
    driver_client.post("/bookings", json={"booking_date": first.isoformat(), "hour": 8})

    both = list_range(driver_client, first, second).json()
    assert [(b["booking_date"], b["hour"]) for b in both] == [
        (first.isoformat(), 8),
        (first.isoformat(), 15),
        (second.isoformat(), 9),
    ]
    # Hranice obdobia sa rátajú vrátane: jednodňový rozsah vráti rezervácie toho dňa.
    only_first = list_range(driver_client, first, first).json()
    assert [b["hour"] for b in only_first] == [8, 15]


def test_list_empty(driver_client):
    day = weekday_in(7)
    resp = list_range(driver_client, day, day)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"start": "2026-11-01"},
        {"end": "2026-11-30"},
        {"start": "2026-11-30", "end": "2026-11-01"},  # koniec pred začiatkom
        {"start": "2026-01-01", "end": "2026-12-31"},  # príliš dlhé obdobie
        {"start": "abc", "end": "2026-11-30"},
    ],
)
def test_list_validation_errors(driver_client, params):
    assert driver_client.get("/bookings", params=params).status_code == 422


def test_list_accepts_longest_allowed_range(driver_client):
    start = date(2026, 11, 1)
    assert (
        list_range(driver_client, start, start + timedelta(days=MAX_RANGE_DAYS)).status_code == 200
    )


# --- Zrušenie rezervácie ---


def test_owner_can_cancel_and_slot_is_free_again(driver_client, other_client):
    booking = driver_client.post("/bookings", json=slot()).json()
    assert driver_client.delete(f"/bookings/{booking['id']}").status_code == 204
    assert driver_client.delete(f"/bookings/{booking['id']}").status_code == 404
    assert other_client.post("/bookings", json=slot()).status_code == 201


def test_user_cannot_cancel_someone_elses_booking(driver_client, other_client):
    booking = driver_client.post("/bookings", json=slot()).json()
    resp = other_client.delete(f"/bookings/{booking['id']}")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "You can cancel only your own bookings"
    day = weekday_in(7)
    assert len(list_range(driver_client, day, day).json()) == 1  # rezervácia ostala


def test_admin_can_cancel_any_booking(driver_client, admin_client):
    booking = driver_client.post("/bookings", json=slot()).json()
    assert admin_client.delete(f"/bookings/{booking['id']}").status_code == 204


def test_cancel_missing_booking_returns_404(driver_client):
    resp = driver_client.delete("/bookings/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Booking not found"


# --- Prihlásenie ---


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/bookings?start=2026-11-01&end=2026-11-30"),
        ("post", "/bookings"),
        ("delete", "/bookings/1"),
    ],
)
def test_bookings_require_login(client, method, url):
    kwargs = {"json": slot()} if method == "post" else {}
    assert getattr(client, method)(url, **kwargs).status_code == 401
