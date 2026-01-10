from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date

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
    car_model: Optional[str] = None
    car_color: Optional[str] = None
    license_plate: Optional[str] = None

class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str

from uuid import UUID

# Properties to return to client (Never return password!)
class UserResponse(UserBase):
    id: UUID
    is_active: bool
    car_model: Optional[str] = None
    car_color: Optional[str] = None
    license_plate: Optional[str] = None
    
    # Rating stats
    average_rating_as_driver: Optional[float] = None
    average_rating_as_passenger: Optional[float] = None
    total_ratings_as_driver: int = 0
    total_ratings_as_passenger: int = 0
    is_top_rated_driver: bool = False
    is_verified_driver: bool = False

    # Profile Fields (Section 11)
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

    # Verification Status
    email_verified: bool
    phone_verified: bool
    sjsu_email_verified: bool
    identity_verified: bool
    sjsu_email: Optional[str] = None

    class Config:
        # Pydantic's 'orm_mode' allows it to read data from SQLAlchemy models
        from_attributes = True

# Profile Update Schema
class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?1?\d{10,15}$')
    bio: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern='^(male|female|other|prefer_not_to_say)$')
    
    # Driver information
    car_model: Optional[str] = Field(None, max_length=100)
    car_color: Optional[str] = Field(None, max_length=50)
    license_plate: Optional[str] = Field(None, max_length=20)

    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) not in [10, 11]:
                raise ValueError('Phone number must be 10 or 11 digits')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class PhoneVerificationRequest(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+?1?\d{10,15}$')

class PhoneVerificationConfirm(BaseModel):
    phone_number: str
    code: str = Field(..., pattern=r'^\d{6}$')

class AccountDeletionRequest(BaseModel):
    password: str = Field(..., description="Confirm password to delete account")
    reason: Optional[str] = Field(None, max_length=500, description="Why are you leaving?")
