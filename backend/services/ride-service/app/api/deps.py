from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from app.core.config import settings

# A simplified security dependency just to get the user ID from the token header (gateway usually handles auth)
# For the MVP, we assume the token is passed and valid logic is similar to user-service.
# However, we are in a diff service. We might verify token signature if we share the secret.
# Let's assume we share the SECRET_KEY in config (passed via env).

from fastapi.security import OAuth2PasswordBearer
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.USER_SERVICE_URL}{settings.API_V1_PREFIX}/auth/login/access-token"
)

async def get_current_user_id(token: str = Depends(reusable_oauth2)) -> str:
    """
    Decodes the JWT token to get the user ID.
    Does NOT query the user database (that's in user-service).
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Could not validate credentials")
        return user_id
    except (JWTError, Exception):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
