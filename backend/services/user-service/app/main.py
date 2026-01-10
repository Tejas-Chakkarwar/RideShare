from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import health

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 1. Setup Logging
# Logging is crucial for debugging in production
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# 2. Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User management and authentication service for SJSU RideShare",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc" # ReDoc UI
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 3. Configure CORS Middleware
# This allows our frontend (running on a different port) to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers (Authorization, etc.)
)

# 4. Middleware & Error Handlers
from app.middleware.logging_middleware import logging_middleware
from app.middleware.error_handler import global_exception_handler

app.middleware("http")(logging_middleware)
app.add_exception_handler(Exception, global_exception_handler)

# 4. Include Routers
# We organize routes into separate modules
app.include_router(health.router, tags=["Health"])
from app.api.routes import auth, users, stripe_connect, saved_locations
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(saved_locations.router, prefix=f"{settings.API_V1_PREFIX}/users/me/saved-locations", tags=["Saved Locations"])
app.include_router(stripe_connect.router, prefix=f"{settings.API_V1_PREFIX}/driver", tags=["Driver Payouts"])

# 5. Startup Event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.SERVICE_NAME}...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")

# Mount uploads directory for static file serving
import os
from fastapi.staticfiles import StaticFiles

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
