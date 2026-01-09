from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class RatingCreate(BaseModel):
    booking_id: UUID
    rated_user_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class RatingResponse(BaseModel):
    id: UUID
    booking_id: UUID
    rater_id: UUID
    rated_user_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
