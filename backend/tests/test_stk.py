from datetime import date, timedelta

import pytest

from app.api.vehicles import STK_SOON_DAYS

VALID = {"brand": "Skoda", "model": "Octavia", "license_plate": "BA123AB"}


def in_days(days: int) -> str:
    """Dátum o daný počet dní od dneška ako text, napr. '2026-11-20' (záporné číslo = minulosť)."""
    return (date.today() + timedelta(days=days)).isoformat()


def test_stk_is_optional(admin_client):
    body = admin_client.post("/vehicles", json=VALID).json()
    assert body["stk_valid_until"] is None


def test_stk_is_stored(admin_client):
    resp = admin_client.post("/vehicles", json={**VALID, "stk_valid_until": "2027-05-31"})
    assert resp.status_code == 201
    assert resp.json()["stk_valid_until"] == "2027-05-31"


@pytest.mark.parametrize("value", ["31.05.2027", "2027-02-30", "zajtra", 20270531])
def test_invalid_stk_date_is_rejected(admin_client, value):
    resp = admin_client.post("/vehicles", json={**VALID, "stk_valid_until": value})
    assert resp.status_code == 422


def test_stk_can_be_set_and_cleared(admin_client, make_vehicle):
    url = f"/vehicles/{make_vehicle()['id']}"
    assert (
        admin_client.patch(url, json={"stk_valid_until": "2027-05-31"}).json()["stk_valid_until"]
        == "2027-05-31"
    )
    # Zmena iného poľa dátum STK nezmaže.
    assert (
        admin_client.patch(url, json={"model": "Fabia"}).json()["stk_valid_until"] == "2027-05-31"
    )
    # Poslaný null ho zmaže.
    assert admin_client.patch(url, json={"stk_valid_until": None}).json()["stk_valid_until"] is None


def test_stats_empty(admin_client):
    resp = admin_client.get("/vehicles/stats")
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "stk_expiring": 0, "stk_expired": 0}


def test_stats_count_expiring_and_expired(admin_client):
    stk_dates = [
        None,  # bez dátumu: ráta sa len do total
        in_days(-400),  # dávno po
        in_days(-1),  # včera skončila -> po
        in_days(0),  # dnes je posledný deň -> ešte platí, končí
        in_days(STK_SOON_DAYS),  # posledný deň, ktorý sa ešte ráta ako "končí"
        in_days(STK_SOON_DAYS + 1),  # o deň neskôr už nie
        in_days(500),
    ]
    for i, stk in enumerate(stk_dates):
        resp = admin_client.post(
            "/vehicles", json={**VALID, "license_plate": f"BA{i}00AA", "stk_valid_until": stk}
        )
        assert resp.status_code == 201

    assert admin_client.get("/vehicles/stats").json() == {
        "total": 7,
        "stk_expiring": 2,
        "stk_expired": 2,
    }


def test_driver_can_read_stats(driver_client):
    assert driver_client.get("/vehicles/stats").status_code == 200


def test_stats_require_login(client):
    assert client.get("/vehicles/stats").status_code == 401
