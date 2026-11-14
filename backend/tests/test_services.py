import pytest

VALID = {"description": "Výmena oleja", "cost": "89.90", "service_date": "2026-11-02"}


def test_create_service(admin_client, make_vehicle):
    vehicle = make_vehicle()
    resp = admin_client.post(f"/vehicles/{vehicle['id']}/services", json=VALID)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["vehicle_id"] == vehicle["id"]
    assert (body["description"], body["cost"], body["service_date"]) == (
        "Výmena oleja",
        "89.90",
        "2026-11-02",
    )


@pytest.mark.parametrize(("sent", "stored"), [(120, "120.00"), (120.5, "120.50"), ("0", "0.00")])
def test_cost_is_stored_with_two_decimals(admin_client, make_vehicle, sent, stored):
    vehicle = make_vehicle()
    admin_client.post(f"/vehicles/{vehicle['id']}/services", json={**VALID, "cost": sent})
    assert admin_client.get(f"/vehicles/{vehicle['id']}/services").json()[0]["cost"] == stored


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "description": ""},
        {**VALID, "description": "   "},
        {**VALID, "description": "x" * 501},
        {**VALID, "cost": "-1"},
        {**VALID, "cost": "10.999"},
        {**VALID, "cost": "100000000"},
        {**VALID, "cost": "NaN"},
        {**VALID, "cost": "abc"},
        {**VALID, "service_date": "02.11.2026"},
        {**VALID, "service_date": "2026-13-01"},
        {"description": "Výmena oleja", "cost": "89.90"},
        {"description": "Výmena oleja", "service_date": "2026-11-02"},
    ],
)
def test_create_validation_errors(admin_client, make_vehicle, payload):
    vehicle = make_vehicle()
    assert admin_client.post(f"/vehicles/{vehicle['id']}/services", json=payload).status_code == 422


def test_list_is_newest_first_and_only_for_that_vehicle(admin_client, make_vehicle):
    first = make_vehicle(license_plate="BA111AA")
    second = make_vehicle(license_plate="BA222BB")
    for service_date in ["2026-01-10", "2026-03-05", "2026-02-20"]:
        admin_client.post(
            f"/vehicles/{first['id']}/services", json={**VALID, "service_date": service_date}
        )
    admin_client.post(f"/vehicles/{second['id']}/services", json=VALID)

    dates = [
        s["service_date"] for s in admin_client.get(f"/vehicles/{first['id']}/services").json()
    ]
    assert dates == ["2026-03-05", "2026-02-20", "2026-01-10"]
    assert len(admin_client.get(f"/vehicles/{second['id']}/services").json()) == 1


def test_list_empty(admin_client, make_vehicle):
    vehicle = make_vehicle()
    resp = admin_client.get(f"/vehicles/{vehicle['id']}/services")
    assert resp.status_code == 200
    assert resp.json() == []


def test_missing_vehicle_returns_404(admin_client):
    assert admin_client.get("/vehicles/999/services").status_code == 404
    resp = admin_client.post("/vehicles/999/services", json=VALID)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Vehicle not found"


def test_delete_service(admin_client, make_vehicle):
    vehicle = make_vehicle()
    url = f"/vehicles/{vehicle['id']}/services"
    service = admin_client.post(url, json=VALID).json()
    assert admin_client.delete(f"{url}/{service['id']}").status_code == 204
    assert admin_client.get(url).json() == []
    resp = admin_client.delete(f"{url}/{service['id']}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Service record not found"


def test_service_cannot_be_deleted_through_another_vehicle(admin_client, make_vehicle):
    first = make_vehicle(license_plate="BA111AA")
    second = make_vehicle(license_plate="BA222BB")
    service = admin_client.post(f"/vehicles/{first['id']}/services", json=VALID).json()

    resp = admin_client.delete(f"/vehicles/{second['id']}/services/{service['id']}")
    assert resp.status_code == 404
    assert len(admin_client.get(f"/vehicles/{first['id']}/services").json()) == 1


def test_deleting_vehicle_deletes_its_services(admin_client, make_vehicle):
    vehicle = make_vehicle()
    admin_client.post(f"/vehicles/{vehicle['id']}/services", json=VALID)
    assert admin_client.delete(f"/vehicles/{vehicle['id']}").status_code == 204

    # Nové auto dostane nové id, staré záznamy sa k nemu nesmú "prilepiť".
    new = make_vehicle()
    assert admin_client.get(f"/vehicles/{new['id']}/services").json() == []


def test_driver_can_read_but_not_write(admin_client, driver_client, make_vehicle):
    vehicle = make_vehicle()
    url = f"/vehicles/{vehicle['id']}/services"
    service = admin_client.post(url, json=VALID).json()

    assert driver_client.get(url).status_code == 200
    assert driver_client.post(url, json=VALID).status_code == 403
    assert driver_client.delete(f"{url}/{service['id']}").status_code == 403
    assert len(admin_client.get(url).json()) == 1


def test_services_require_login(client, admin_client, make_vehicle):
    vehicle = make_vehicle()
    assert client.get(f"/vehicles/{vehicle['id']}/services").status_code == 401
