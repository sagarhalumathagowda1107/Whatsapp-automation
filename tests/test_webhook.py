from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models.message_log import WhatsAppMessageLog, MessageLogStatus

def test_webhook_verification_success(client: TestClient):
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "1158201444",
        "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN
    }
    res = client.get("/api/v1/whatsapp/webhook", params=params)
    assert res.status_code == 200
    assert res.text == "1158201444"

def test_webhook_verification_failure(client: TestClient):
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "1158201444",
        "hub.verify_token": "wrong_verify_token"
    }
    res = client.get("/api/v1/whatsapp/webhook", params=params)
    assert res.status_code == 403

def test_webhook_event_status_processing(client: TestClient, db: Session):
    # Pre-populate a message log with a specific wamid
    wamid = "wamid.TEST_EVENT_ID_001"
    log = WhatsAppMessageLog(
        whatsapp_message_id=wamid,
        status="sent"
    )
    db.add(log)
    db.commit()

    # Send Meta Webhook delivery status update
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "statuses": [
                                {
                                    "id": wamid,
                                    "status": "delivered",
                                    "timestamp": "1700000000",
                                    "recipient_id": "14155552671"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    res = client.post("/api/v1/whatsapp/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    # Refresh DB session & verify status updated to 'delivered'
    db.refresh(log)
    assert log.status == "delivered"
    assert log.delivered_at is not None
