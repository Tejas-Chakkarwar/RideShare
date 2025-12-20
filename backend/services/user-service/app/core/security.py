from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# 1. Password Hashing Context
# verifying "bcrypt" is the industry standard for safe password storage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Key Constants
ALGORITHM = "HS256"
# In a real app, this key should be VERY long and secret. 
# We'll expect it to be passed via environment variables (pydantic settings)
# For now, we will add a default to Config if missing, or handle it there.

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """
    Generate a JSON Web Token (JWT)
    
    The token contains:
    - sub: The subject (user_id)
    - exp: Expiration time
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Default 15 mins
        
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if the typed password matches the stored hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a password so we can safely store it in the database.
    """
    return pwd_context.hash(password)
