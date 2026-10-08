import pytest
from fastapi.testclient import TestClient

def test_create_psf_record(client: TestClient, auth_headers: dict):
    payload = {
        "title": "Q3 Infrastructure Upgrade",
        "description": "Upgraded database cluster to PostgreSQL 16",
        "category": "Infrastructure",
        "value": {"uptime": "99.99%", "cost_savings": 1500},
        "status": "COMPLETED"
    }
    response = client.post("/api/v1/psf", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["category"] == "Infrastructure"
    assert "id" in data

def test_list_and_filter_psf_records(client: TestClient, auth_headers: dict):
    # Create 2 items
    client.post("/api/v1/psf", json={"title": "Item A", "category": "DevOps", "status": "ACTIVE"}, headers=auth_headers)
    client.post("/api/v1/psf", json={"title": "Item B", "category": "Security", "status": "COMPLETED"}, headers=auth_headers)

    # Filter by category
    res = client.get("/api/v1/psf?category=DevOps", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["title"] == "Item A"

    # Filter by search query
    res_search = client.get("/api/v1/psf?q=Item B", headers=auth_headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1

def test_update_and_delete_psf_record(client: TestClient, auth_headers: dict):
    res_create = client.post("/api/v1/psf", json={"title": "Original Title", "category": "General"}, headers=auth_headers)
    psf_id = res_create.json()["id"]

    # Update
    res_update = client.patch(f"/api/v1/psf/{psf_id}", json={"title": "Updated Title"}, headers=auth_headers)
    assert res_update.status_code == 200
    assert res_update.json()["title"] == "Updated Title"

    # Delete
    res_del = client.delete(f"/api/v1/psf/{psf_id}", headers=auth_headers)
    assert res_del.status_code == 204

    # Verify not found
    res_get = client.get(f"/api/v1/psf/{psf_id}", headers=auth_headers)
    assert res_get.status_code == 404

def test_psf_unauthorized_access(client: TestClient):
    res = client.get("/api/v1/psf")
    assert res.status_code == 401
