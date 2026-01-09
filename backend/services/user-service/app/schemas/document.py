from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    document_type: str
    file_url: str
    status: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
