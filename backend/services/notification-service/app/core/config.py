"""
Notification Service Configuration

Manages settings for SendGrid email, Firebase push notifications,
and notification service behavior.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Notification service settings"""

    # Service Info
    APP_NAME: str = "SJSU RideShare - Notification Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/rideshare_notifications"

    # SendGrid Email
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@sjsurideshare.com"
    SENDGRID_FROM_NAME: str = "SJSU RideShare"

    # Firebase Push Notifications
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_ENABLED: bool = False  # Set to True when Firebase is configured

    # External Services
    USER_SERVICE_URL: str = "http://localhost:8001"
    RIDE_SERVICE_URL: str = "http://localhost:8002"
    BOOKING_SERVICE_URL: str = "http://localhost:8003"

    # App URLs (for deep linking)
    APP_URL: str = "https://app.sjsurideshare.com"
    WEB_URL: str = "https://sjsurideshare.com"

    # Notification Settings
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 60

    # Template Settings
    TEMPLATE_DIR: str = "app/templates/email"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
