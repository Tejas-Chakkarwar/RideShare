from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import health

# 1. Setup Logging
# Logging is crucial for debugging in production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2. Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User management and authentication service for SJSU RideShare",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc" # ReDoc UI
)

# 3. Configure CORS Middleware
# This allows our frontend (running on a different port) to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers (Authorization, etc.)
)

# 4. Include Routers
# We organize routes into separate modules
app.include_router(health.router, tags=["Health"])
from app.api.routes import auth, users
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])

# 5. Startup Event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.SERVICE_NAME}...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
