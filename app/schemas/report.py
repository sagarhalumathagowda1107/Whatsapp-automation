from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.recipient import RecipientResponse

class ReportGenerateRequest(BaseModel):
    start_date: datetime | None = Field(None, description="Start date of reporting period (default: 7 days ago)")
    end_date: datetime | None = Field(None, description="End date of reporting period (default: now)")
    send_immediately: bool = Field(False, description="Send immediately to active recipients after generation")

class WhatsAppMessageLogResponse(BaseModel):
    id: str
    recipient_id: str | None
    whatsapp_message_id: str | None
    status: str
    error_code: str | None
    error_message: str | None
    request_timestamp: datetime
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class ReportResponse(BaseModel):
    id: str
    report_period_start: datetime
    report_period_end: datetime
    filename: str
    file_path: str
    status: str
    generated_at: datetime
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReportDetailResponse(ReportResponse):
    message_logs: List[WhatsAppMessageLogResponse] = []
