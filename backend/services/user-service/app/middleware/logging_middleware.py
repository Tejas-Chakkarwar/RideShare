from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """
    Middleware to log all incoming requests
    Logs: method, path, client IP, status code, processing time
    """
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.2f}ms"
    )
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response
