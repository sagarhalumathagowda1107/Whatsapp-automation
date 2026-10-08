from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.report import ReportStatus

def test_generate_and_send_report_flow(client: TestClient, auth_headers: dict):
    # 1. Create a recipient first
    rec_payload = {"name": "Test Recipient", "phone_number": "+14155559876", "active": True}
    client.post("/api/v1/recipients", json=rec_payload, headers=auth_headers)

    # 2. Create PSF record
    psf_payload = {"title": "Weekly Goal", "category": "Sales", "status": "ACTIVE"}
    client.post("/api/v1/psf", json=psf_payload, headers=auth_headers)

    # 3. Generate report manually with send_immediately=True
    gen_payload = {"send_immediately": True}
    res_gen = client.post("/api/v1/reports/generate", json=gen_payload, headers=auth_headers)
    assert res_gen.status_code == 201
    report_data = res_gen.json()
    assert report_data["status"] == ReportStatus.SENT.value
    report_id = report_data["id"]

    # 4. Fetch detailed report view
    res_detail = client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert len(detail["message_logs"]) == 1
    assert detail["message_logs"][0]["status"] == "sent"

def test_retry_failed_report_deliveries(client: TestClient, auth_headers: dict):
    # Generate report without sending immediately
    res_gen = client.post("/api/v1/reports/generate", json={"send_immediately": False}, headers=auth_headers)
    assert res_gen.status_code == 201
    report_id = res_gen.json()["id"]

    # Send report
    res_send = client.post(f"/api/v1/reports/{report_id}/send", headers=auth_headers)
    assert res_send.status_code == 200

    # Retry endpoint
    res_retry = client.post(f"/api/v1/reports/{report_id}/retry", headers=auth_headers)
    assert res_retry.status_code == 200
