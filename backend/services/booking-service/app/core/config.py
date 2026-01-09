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
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8004"

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Email (SendGrid for MVP, AWS SES for production)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@sjsurideshare.com"
    SENDGRID_FROM_NAME: str = "SJSU RideShare"

    # App URL for email links
    APP_URL: str = "http://localhost:3000"

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8081"
    ]

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
