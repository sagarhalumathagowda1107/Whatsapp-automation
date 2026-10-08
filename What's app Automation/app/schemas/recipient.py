import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

def normalize_phone(v: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', v)
    if not cleaned:
        raise ValueError("Phone number cannot be empty")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    if not re.match(r'^\+[1-9]\d{6,14}$', cleaned):
        raise ValueError("Phone number must be a valid E.164 formatted string e.g. +1234567890")
    return cleaned

class RecipientBase(BaseModel):
    name: str = Field(..., max_length=255, description="Full name of recipient")
    phone_number: str = Field(..., description="Phone number in E.164 format (+1234567890)")
    active: bool = Field(True, description="Whether recipient should receive automated reports")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone(v)

class RecipientCreate(RecipientBase):
    pass

class RecipientUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    phone_number: str | None = None
    active: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            return normalize_phone(v)
        return v

class RecipientResponse(RecipientBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
