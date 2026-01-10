from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class RideTemplate(Base):
    """Template for frequently created rides"""
    __tablename__ = "ride_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(100), nullable=False)  # "Mon/Wed to SJSU"
    template_data = Column(JSON, nullable=False)  # Stores full ride creation data

    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
