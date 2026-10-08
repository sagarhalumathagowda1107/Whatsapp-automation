from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class PSFBase(BaseModel):
    title: str = Field(..., max_length=255, description="Title of the PSF record")
    description: str | None = Field(None, description="Detailed description")
    category: str = Field("General", max_length=100, description="Category of report metric")
    value: Any = Field(None, description="Value or data payload (number, object, text)")
    status: str = Field("ACTIVE", max_length=50, description="Status (ACTIVE, PENDING, COMPLETED, etc.)")

class PSFCreate(PSFBase):
    pass

class PSFUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    value: Any = None
    status: str | None = Field(None, max_length=50)

class PSFResponse(PSFBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
