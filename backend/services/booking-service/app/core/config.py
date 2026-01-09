from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service Info
    PROJECT_NAME: str = "RideShare Booking Service"
    SERVICE_NAME: str = "booking-service"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str

    # Service Communication
    RIDE_SERVICE_URL: str
    USER_SERVICE_URL: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Email (SendGrid for MVP, AWS SES for production)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@sjsurideshare.com"
    SENDGRID_FROM_NAME: str = "SJSU RideShare"

    # App URL for email links
    APP_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
