from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

# Common properties
class SavedLocationBase(BaseModel):
    name: str = Field(..., max_length=50)
    address: str = Field(..., max_length=500)
    lat: float
    lng: float
    category: str = Field(..., pattern="^(home|work|school|custom)$")
    icon: Optional[str] = "location_pin"

# Properties to receive on create
class SavedLocationCreate(SavedLocationBase):
    pass

# Properties to receive on update
class SavedLocationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    lat: Optional[float] = None
    lng: Optional[float] = None
    category: Optional[str] = Field(None, pattern="^(home|work|school|custom)$")
    icon: Optional[str] = None
    usage_count: Optional[int] = None

# Properties to return to client
class SavedLocationResponse(SavedLocationBase):
    id: UUID
    user_id: UUID
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True
