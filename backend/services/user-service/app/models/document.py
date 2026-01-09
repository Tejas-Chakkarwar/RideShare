from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    document_type = Column(Enum("license", "insurance", "vehicle", "profile_photo", name="document_type_enum"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    status = Column(Enum("pending", "approved", "rejected", name="document_status_enum"), default="pending")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
