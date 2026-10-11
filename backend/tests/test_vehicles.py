from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

from app.db.session import engine

VALID = {"brand": "Skoda", "model": "Octavia", "license_plate": "BA123AB"}


def test_create_vehicle(client):
    resp = client.post("/vehicles", json=VALID)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert (body["brand"], body["model"], body["license_plate"]) == ("Skoda", "Octavia", "BA123AB")


def test_created_at_is_timezone_aware(client):
    body = client.post("/vehicles", json=VALID).json()
    created = datetime.fromisoformat(body["created_at"])
    assert created.utcoffset() == timedelta(0)


@pytest.mark.parametrize("plate", [" ba 123 ab ", "BA-123AB", "ba - 123 - ab"])
def test_license_plate_is_normalized(client, plate):
    body = client.post("/vehicles", json={**VALID, "license_plate": plate}).json()
    assert body["license_plate"] == "BA123AB"


def test_plate_length_is_checked_after_normalization(client):
    plate = "AB CD EF GH IJ KL MN OP QR ST"  # 29 znakov, po odstránení medzier 20
    resp = client.post("/vehicles", json={**VALID, "license_plate": plate})
    assert resp.status_code == 201
    assert resp.json()["license_plate"] == "ABCDEFGHIJKLMNOPQRST"


def test_whitespace_is_stripped_from_names(client):
    body = client.post("/vehicles", json={**VALID, "brand": "  Skoda  "}).json()
    assert body["brand"] == "Skoda"


@pytest.mark.parametrize("plate", ["BA 123 AB", "ba123ab", "Ba123Ab", "BA-123AB", "ba-123-ab"])
def test_duplicate_plate_is_rejected_regardless_of_formatting(client, make_vehicle, plate):
    make_vehicle(license_plate="BA123AB")
    resp = client.post("/vehicles", json={**VALID, "license_plate": plate})
    assert resp.status_code == 409
    assert resp.json()["detail"] == "A vehicle with this license plate already exists"


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "brand": ""},
        {**VALID, "brand": "   "},
        {**VALID, "model": "x" * 51},
        {**VALID, "license_plate": "BA#123"},
        {**VALID, "license_plate": "X" * 21},
        {**VALID, "license_plate": ""},
        {**VALID, "license_plate": "---"},
        {**VALID, "license_plate": " - - "},
        {"brand": "Skoda", "model": "Octavia"},
    ],
)
def test_create_validation_errors(client, payload):
    assert client.post("/vehicles", json=payload).status_code == 422


def test_get_vehicle(client, make_vehicle):
    created = make_vehicle()
    resp = client.get(f"/vehicles/{created['id']}")
    assert resp.status_code == 200
    assert resp.json() == created


def test_get_missing_vehicle_returns_404(client):
    resp = client.get("/vehicles/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Vehicle not found"


def test_list_is_paginated(client, make_vehicle):
    for i in range(5):
        make_vehicle(license_plate=f"BA{i}00AA")

    page = client.get("/vehicles", params={"skip": 1, "limit": 2}).json()
    assert page["total"] == 5
    assert (page["skip"], page["limit"]) == (1, 2)
    assert [v["id"] for v in page["items"]] == [2, 3]


def test_list_shows_old_rows_that_fail_input_validation(client):
    # Prvá verzia API povoľovala aj ŠPZ ako 'BA#1'. Výstup ich musí vedieť vypísať.
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO vehicles (brand, model, license_plate) VALUES ('', 'x', 'BA#1')")
        )
    resp = client.get("/vehicles")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["license_plate"] == "BA#1"


def test_list_empty(client):
    assert client.get("/vehicles").json() == {"items": [], "total": 0, "skip": 0, "limit": 100}


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"skip": -1}, {"skip": 10**19}])
def test_list_rejects_bad_pagination(client, params):
    assert client.get("/vehicles", params=params).status_code == 422


@pytest.mark.parametrize("vehicle_id", [0, -1, 2**31, 10**19])
def test_out_of_range_vehicle_id_is_rejected(client, vehicle_id):
    url = f"/vehicles/{vehicle_id}"
    assert client.get(url).status_code == 422
    assert client.patch(url, json={"model": "Fabia"}).status_code == 422
    assert client.delete(url).status_code == 422


def test_partial_update(client, make_vehicle):
    created = make_vehicle()
    resp = client.patch(f"/vehicles/{created['id']}", json={"model": "Fabia"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "Fabia"
    assert body["brand"] == created["brand"]
    assert body["license_plate"] == created["license_plate"]


def test_update_normalizes_plate(client, make_vehicle):
    created = make_vehicle()
    resp = client.patch(f"/vehicles/{created['id']}", json={"license_plate": "ke 999 zz"})
    assert resp.json()["license_plate"] == "KE999ZZ"


@pytest.mark.parametrize("field", ["brand", "model", "license_plate"])
def test_update_rejects_null(client, make_vehicle, field):
    created = make_vehicle()
    assert client.patch(f"/vehicles/{created['id']}", json={field: None}).status_code == 422


def test_update_to_existing_plate_returns_409(client, make_vehicle):
    make_vehicle(license_plate="BA111AA")
    second = make_vehicle(license_plate="BA222BB")
    resp = client.patch(f"/vehicles/{second['id']}", json={"license_plate": "ba 111 aa"})
    assert resp.status_code == 409


def test_update_with_own_plate_is_allowed(client, make_vehicle):
    created = make_vehicle()
    resp = client.patch(f"/vehicles/{created['id']}", json={"license_plate": "BA123AB"})
    assert resp.status_code == 200


def test_update_missing_vehicle_returns_404(client):
    assert client.patch("/vehicles/999", json={"model": "Fabia"}).status_code == 404


def test_delete_vehicle(client, make_vehicle):
    created = make_vehicle()
    assert client.delete(f"/vehicles/{created['id']}").status_code == 204
    assert client.get(f"/vehicles/{created['id']}").status_code == 404
    assert client.delete(f"/vehicles/{created['id']}").status_code == 404
