"""
Health Check Routes
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat()
    }
