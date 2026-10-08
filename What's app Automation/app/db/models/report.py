import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.message_log import WhatsAppMessageLog

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ReportStatus(str, Enum):
    GENERATED = "GENERATED"
    SENDING = "SENDING"
    SENT = "SENT"
    PARTIALLY_SENT = "PARTIALLY_SENT"
    FAILED = "FAILED"

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    report_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ReportStatus.GENERATED.value, index=True)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    message_logs: Mapped[List["WhatsAppMessageLog"]] = relationship("WhatsAppMessageLog", back_populates="report", cascade="all, delete-orphan")
