from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class RideTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    template_data: Dict[str, Any]

class RideTemplateCreate(RideTemplateBase):
    pass

class RideTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    template_data: Optional[Dict[str, Any]] = None

class RideTemplateResponse(RideTemplateBase):
    id: UUID
    driver_id: UUID
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True
