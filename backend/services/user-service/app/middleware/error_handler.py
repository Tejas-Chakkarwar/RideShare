from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import traceback
from app.core.config import settings

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions
    Returns structured JSON error response
    Logs full traceback for debugging
    """
    # Log the exception
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # Create error response
    error_response = {
        "error": type(exc).__name__,
        "message": "An internal error occurred",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": str(request.url)
    }
    
    # Include details in debug mode
    if settings.DEBUG:
        error_response["detail"] = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )
