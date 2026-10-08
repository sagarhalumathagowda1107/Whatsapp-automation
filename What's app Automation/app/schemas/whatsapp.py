from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field

class WebhookVerificationQuery(BaseModel):
    hub_mode: str = Field(..., alias="hub.mode")
    hub_challenge: str = Field(..., alias="hub.challenge")
    hub_verify_token: str = Field(..., alias="hub.verify_token")

class WhatsAppStatusValue(BaseModel):
    id: str  # WhatsApp Message ID
    status: str  # sent, delivered, read, failed
    timestamp: str | int
    recipient_id: str | None = None
    errors: List[Dict[str, Any]] | None = None

class WhatsAppChangeValue(BaseModel):
    messaging_product: str | None = None
    metadata: Dict[str, Any] | None = None
    statuses: List[WhatsAppStatusValue] | None = None
    messages: List[Dict[str, Any]] | None = None

class WhatsAppChange(BaseModel):
    value: WhatsAppChangeValue
    field: str

class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]

class WebhookEventPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]
