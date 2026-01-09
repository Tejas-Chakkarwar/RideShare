from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from uuid import UUID
from app.core.config import settings

# Point to User Service for token generation in Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.USER_SERVICE_URL}{settings.API_V1_PREFIX}/auth/login/access-token"
)

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """
    Validate JWT token and return user_id (sub).
    Does NOT hit the database, only verifies signature.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        return UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
