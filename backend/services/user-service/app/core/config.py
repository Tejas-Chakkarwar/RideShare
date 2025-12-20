from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application Configuration
    
    We use Pydantic Settings to automatically read environment variables.
    This ensures type safety (e.g., verifying DEBUG is a boolean).
    """
    # Service Info
    SERVICE_NAME: str = "user-service"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str = "temporary_secret_key_for_dev_only_change_in_prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SJSU RideShare"
    
    # CORS (Cross-Origin Resource Sharing)
    # Defines which domains can talk to this API
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",   # Frontend dev server
        "http://localhost:8081"    # React Native Metro bundler
    ]
    
    class Config:
        # Reads from .env file if available
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()
