from fastapi import WebSocket, status, Query
from jose import jwt, JWTError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def authenticate_websocket(
    websocket: WebSocket,
    token: str = Query(...)
) -> dict:
    """
    Authenticate WebSocket connection using JWT token
    
    Returns:
        dict with user_id and email if valid
    
    Raises:
        Closes WebSocket with 4008 if invalid
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Depending on how the token was created (sub=user_id usually)
        user_id = payload.get("sub")
        
        # Some tokens might put payload differently? In our user service:
        # to_encode = {"exp": expire, "sub": str(subject)}
        # So "sub" is the user_id.
        
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise Exception("Invalid token payload")
        
        return {
            "user_id": user_id,
            "email": payload.get("email", "") # Might not be in token but that's okay
        }
    
    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise Exception("Invalid or expired token")
