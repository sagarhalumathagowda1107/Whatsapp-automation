from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.api.deps import verify_admin_api_key
from app.db.models.message_log import WhatsAppMessageLog, MessageLogStatus
from app.schemas.whatsapp import WebhookEventPayload
from app.services.whatsapp_service import whatsapp_service, WhatsAppServiceError
from app.utils.logger import logger

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhook & Integration"])

@router.get("/webhook", summary="Meta Webhook Verification Endpoint")
def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Official Meta WhatsApp Webhook verification endpoint.
    Meta sends a GET request to verify token ownership when setting up the Webhook.
    """
    logger.info(f"Webhook verification requested with mode='{hub_mode}'")
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verification succeeded!")
        return Response(content=hub_challenge, media_type="text/plain")
    
    logger.warning("Webhook verification failed: Invalid verify token or mode")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")

@router.post("/webhook", summary="Meta Webhook Event Receiver")
async def receive_webhook_event(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives real-time status updates (sent, delivered, read, failed) from Meta WhatsApp Cloud API.
    """
    try:
        body = await request.json()
    except Exception:
        logger.warning("Invalid JSON body received on webhook")
        return {"status": "ignored"}

    logger.debug(f"Webhook event received: {body}")

    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            statuses = value.get("statuses", [])

            for st in statuses:
                wamid = st.get("id")
                msg_status = st.get("status")  # sent, delivered, read, failed
                timestamp_str = st.get("timestamp")
                
                if not wamid or not msg_status:
                    continue

                # Parse timestamp if available
                event_dt = datetime.now(timezone.utc)
                if timestamp_str:
                    try:
                        event_dt = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
                    except (ValueError, TypeError):
                        pass

                # Find log record by WhatsApp Message ID
                log = db.scalar(
                    select(WhatsAppMessageLog).where(WhatsAppMessageLog.whatsapp_message_id == wamid)
                )

                if log:
                    log.status = msg_status
                    if msg_status == "sent" and not log.sent_at:
                        log.sent_at = event_dt
                    elif msg_status == "delivered":
                        log.delivered_at = event_dt
                    elif msg_status == "read":
                        log.read_at = event_dt
                    elif msg_status == "failed":
                        errors = st.get("errors", [])
                        if errors:
                            err_obj = errors[0]
                            log.error_code = str(err_obj.get("code", "UNKNOWN"))
                            log.error_message = err_obj.get("title", "Delivery Failed")
                    
                    db.commit()
                    logger.info(f"Updated WhatsApp Message Log {log.id} status to '{msg_status}' for WAMID {wamid}")

    return {"status": "ok"}

@router.post("/test-send", summary="Send Test WhatsApp Document or Message")
async def send_test_message(
    to_phone: str = Query(..., description="Target phone number in E.164 format (+1234567890)"),
    message: Optional[str] = Query("Hello! This is a test message from WhatsApp PDF Report Automation System.", description="Test text message"),
    _: str = Depends(verify_admin_api_key)
):
    """Admin endpoint to test WhatsApp Cloud API connectivity by sending a text message."""
    try:
        res = await whatsapp_service.send_text_message(to_phone=to_phone, message_body=message)
        return {
            "status": "success",
            "meta_response": res
        }
    except WhatsAppServiceError as err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(err))
