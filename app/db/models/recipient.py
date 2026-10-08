import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.message_log import WhatsAppMessageLog

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Recipient(Base):
    __tablename__ = "recipients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    message_logs: Mapped[List["WhatsAppMessageLog"]] = relationship("WhatsAppMessageLog", back_populates="recipient", cascade="all, delete-orphan")
