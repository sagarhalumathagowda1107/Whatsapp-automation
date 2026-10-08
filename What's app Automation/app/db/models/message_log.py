import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.report import Report
    from app.db.models.recipient import Recipient

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MessageLogStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class WhatsAppMessageLog(Base):
    __tablename__ = "whatsapp_message_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("recipients.id", ondelete="SET NULL"), nullable=True, index=True)
    
    whatsapp_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=MessageLogStatus.PENDING.value, index=True)
    
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    request_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    report: Mapped["Report | None"] = relationship("Report", back_populates="message_logs")
    recipient: Mapped["Recipient | None"] = relationship("Recipient", back_populates="message_logs")
