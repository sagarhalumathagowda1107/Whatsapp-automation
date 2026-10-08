import pytest
from fastapi.testclient import TestClient

def test_create_and_list_recipients(client: TestClient, auth_headers: dict):
    payload = {
        "name": "Alice Smith",
        "phone_number": "+14155552671",
        "active": True
    }
    res = client.post("/api/v1/recipients", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Alice Smith"
    assert data["phone_number"] == "+14155552671"

    # List active
    res_list = client.get("/api/v1/recipients?active_only=true", headers=auth_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

def test_recipient_phone_number_normalization(client: TestClient, auth_headers: dict):
    payload = {
        "name": "Bob Johnson",
        "phone_number": "1 415 555-0199",  # Should normalize to +14155550199
        "active": True
    }
    res = client.post("/api/v1/recipients", json=payload, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["phone_number"] == "+14155550199"

def test_recipient_invalid_phone(client: TestClient, auth_headers: dict):
    payload = {
        "name": "Invalid Recipient",
        "phone_number": "not-a-phone-number"
    }
    res = client.post("/api/v1/recipients", json=payload, headers=auth_headers)
    assert res.status_code == 422  # Pydantic validation failure
