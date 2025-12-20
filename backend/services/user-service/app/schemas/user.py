from typing import Optional
from pydantic import BaseModel, EmailStr

# -------------------
# Token Schemas
# -------------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None

# -------------------
# User Schemas
# -------------------

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties to return to client (Never return password!)
class UserResponse(UserBase):
    id: int
    is_active: bool
    
    class Config:
        # Pydantic's 'orm_mode' allows it to read data from SQLAlchemy models
        from_attributes = True
