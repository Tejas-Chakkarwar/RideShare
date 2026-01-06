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

    class Config:
        env_file = ".env"

settings = Settings()
