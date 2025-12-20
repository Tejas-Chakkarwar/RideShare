from fastapi import APIRouter, status
from datetime import datetime
import asyncpg
import redis.asyncio as redis
from app.core.config import settings

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health Check Endpoint
    
    This endpoint checks if the service and its dependencies (Database, Redis)
    are reachable. It is used by Docker and monitoring tools.
    """
    health_status = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check Database Connection
    try:
        # asyncpg requires 'postgresql://' or 'postgres://', but SQLAlchemy uses 'postgresql+asyncpg://'
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)
        await conn.close()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["checks"]["database"] = f"disconnected: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis Connection
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        health_status["checks"]["redis"] = "connected"
    except Exception as e:
        health_status["checks"]["redis"] = f"disconnected: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status
