from sqlalchemy import Column, String, Float
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class User(Base):
    """
    Read-only mapping of users table for search joins.
    Schema managed by user-service.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    average_rating_as_driver = Column(Float, default=0.0)
    gender = Column(String)
