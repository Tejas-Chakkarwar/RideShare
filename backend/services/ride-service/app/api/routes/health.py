from fastapi import APIRouter, status
from datetime import datetime
from app.core.database import verify_database_connection
from app.core.config import settings

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint
    """
    health_status = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check Database
    if await verify_database_connection():
        health_status["checks"]["database"] = "connected"
    else:
        health_status["checks"]["database"] = "disconnected"
        health_status["status"] = "unhealthy"
        
    return health_status
