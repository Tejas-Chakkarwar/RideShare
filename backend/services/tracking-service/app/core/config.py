from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RideShare Tracking Service"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Auth
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Service URLs
    RIDE_SERVICE_URL: str = "http://ride-service:8000"
    BOOKING_SERVICE_URL: str = "http://booking-service:8000"
    
    class Config:
        case_sensitive = True

settings = Settings()
