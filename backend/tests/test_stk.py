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


def test_list_can_be_filtered_by_stk(admin_client):
    # Tie isté hraničné dátumy ako pri štatistikách: zoznam a čísla na dashboarde musia sedieť.
    stk_dates = {
        "BA000AA": None,
        "BA100AA": in_days(-1),
        "BA200AA": in_days(0),
        "BA300AA": in_days(STK_SOON_DAYS),
        "BA400AA": in_days(STK_SOON_DAYS + 1),
    }
    for plate, stk in stk_dates.items():
        resp = admin_client.post(
            "/vehicles", json={**VALID, "license_plate": plate, "stk_valid_until": stk}
        )
        assert resp.status_code == 201

    def plates(query: str) -> list[str]:
        return [v["license_plate"] for v in admin_client.get(f"/vehicles{query}").json()["items"]]

    assert plates("?stk=expired") == ["BA100AA"]
    assert plates("?stk=expiring") == ["BA200AA", "BA300AA"]
    assert len(plates("")) == 5  # bez filtra príde všetko


def test_stk_filter_counts_only_matching_vehicles(admin_client):
    for i in range(3):
        admin_client.post(
            "/vehicles",
            json={**VALID, "license_plate": f"BA{i}00AA", "stk_valid_until": in_days(-1)},
        )
    admin_client.post("/vehicles", json={**VALID, "license_plate": "BA900AA"})

    # total ráta len vyfiltrované autá (nie všetky 4), aby stránkovanie sedelo.
    body = admin_client.get("/vehicles", params={"stk": "expired", "limit": 2}).json()
    assert body["total"] == 3
    assert len(body["items"]) == 2

    body = admin_client.get("/vehicles", params={"stk": "expired", "limit": 2, "skip": 2}).json()
    assert [v["license_plate"] for v in body["items"]] == ["BA200AA"]


def test_unknown_stk_filter_is_rejected(admin_client):
    assert admin_client.get("/vehicles?stk=hocico").status_code == 422


def test_driver_cannot_read_stats(driver_client):
    assert driver_client.get("/vehicles/stats").status_code == 403


def test_stats_require_login(client):
    assert client.get("/vehicles/stats").status_code == 401
