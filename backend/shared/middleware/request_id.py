"""
Request ID Tracking Middleware
Adds X-Request-ID header to all requests for distributed tracing.
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track requests across services with unique IDs.
    
    Usage:
        from shared.middleware.request_id import RequestIDMiddleware
        app.add_middleware(RequestIDMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check if request already has an ID (from upstream service)
        request_id = request.headers.get("X-Request-ID")
        
        # Generate new ID if not present
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Add to request state for access in route handlers
        request.state.request_id = request_id
        
        # Log request with ID
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        # Process request
        response: Response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
