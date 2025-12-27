from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Ride Service Configuration
    """
    # Service Info
    SERVICE_NAME: str = "ride-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    DATABASE_URL: str
    
    # Inter-service Communication
    USER_SERVICE_URL: str = "http://user-service:8000"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SJSU RideShare Ride Service"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
