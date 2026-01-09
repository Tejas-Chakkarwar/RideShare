from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from uuid import UUID
from app.core import security
from app.core.config import settings

# Usually points to the auth service login endpoint
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.USER_SERVICE_URL}/api/v1/auth/login" 
)

async def get_current_user_id(
    token: str = Depends(oauth2_scheme)
) -> UUID:
    """
    Decodes the JWT token to get the current user ID.
    Does not hit the database or user-service, just verifies signature.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
