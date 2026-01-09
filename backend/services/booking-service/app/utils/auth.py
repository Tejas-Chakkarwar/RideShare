from datetime import datetime
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.USER_SERVICE_URL}/api/v1/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """
    Validate JWT token and return user_id.
    Does not fetch full user object, just extracts ID from token.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user_id = UUID(user_id_str)
        except ValueError:
             # Handle integer IDs (legacy) or invalid UUIDs
             # If legacy int ID, we might need to handle differently or assume str
             # Our system checks assume UUID now for User ID refactor.
             # If it's an int, try to parse? No, UUID(int) works but creates specific UUID.
             # We assume payload 'sub' is the string representation of UUID.
             user_id = UUID(user_id_str)
             
        return user_id
        
    except (JWTError, ValidationError, ValueError) as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
