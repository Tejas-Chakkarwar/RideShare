from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Request
import shutil
import os
from app.models.document import Document
from app.schemas.document import DocumentResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core import security
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, UserProfileUpdate,
    UserPasswordUpdate, PhoneVerificationRequest, PhoneVerificationConfirm,
    PasswordResetRequest, PasswordResetConfirm, AccountDeletionRequest
)
from app.services.profile_service import profile_service
from app.services.verification_service import verification_service
from app.main import limiter

router = APIRouter()

@router.post("/", response_model=UserResponse)
@limiter.limit("3/minute")  # Max 3 registrations per minute
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create new user.
    """
    # 1. Check if user already exists
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this user name already exists in the system.",
        )
    
    # 2. Create new user object
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
    )
    
    # 3. Save to DB
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

from uuid import UUID

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user by ID (for inter-service communication).
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/fcm-token", status_code=status.HTTP_200_OK)
async def update_fcm_token(
    fcm_token: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update FCM token for push notifications.
    Mobile app should call this on:
    - Login
    - App startup
    - Token refresh
    """
    current_user.fcm_token = fcm_token
    db.add(current_user)
    await db.commit()

    return {
        "success": True,
        "message": "FCM token updated successfully"
    }

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update own profile.
    """
    if user_in.email and user_in.email != current_user.email:
        # Check if email is taken
        query = select(User).where(User.email == user_in.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
    
    # Update profile fields via service
    # Note: Service handles commit
    updated_user = await profile_service.update_profile(current_user.id, user_in, db)

    # Handle email update manually if present (Service ignores email)
    if user_in.email and user_in.email != current_user.email:
         current_user.email = user_in.email
         current_user.email_verified = False
         db.add(current_user)
         await db.commit()
         await db.refresh(current_user)
         return current_user
         
    return updated_user



@router.put("/me/password", response_model=Any)
async def update_password(
    *,
    db: AsyncSession = Depends(get_db),
    password_in: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update own password.
    """
    """
    Update own password.
    """
    return await profile_service.change_password(current_user.id, password_in, db)

@router.put("/{user_id}/stripe-customer", status_code=status.HTTP_200_OK)
async def update_stripe_customer(
    user_id: UUID,
    customer_id: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update Stripe Customer ID.
    Called by Booking Service when creating a customer.
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.stripe_customer_id = customer_id
    db.add(user)
    await db.commit()
    
    return {"success": True}

@router.put("/{user_id}/rating-stats", status_code=status.HTTP_200_OK)
async def update_rating_stats(
    user_id: UUID,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update User Rating Statistics (Internal Endpoint).
    Called by Booking Service after a rating is submitted.
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    rating_type = payload.get("rating_type")
    average_rating = payload.get("average_rating")
    total_ratings = payload.get("total_ratings")
    
    if rating_type == "driver":
        user.average_rating_as_driver = average_rating
        user.total_ratings_as_driver = total_ratings
        
        # Check for badges logic if needed, e.g. Top Rated Driver
        if average_rating >= 4.8 and total_ratings >= 50:
            user.is_top_rated_driver = True
        else:
            user.is_top_rated_driver = False
            
    elif rating_type == "passenger":
        user.average_rating_as_passenger = average_rating
        user.total_ratings_as_passenger = total_ratings
    
    db.add(user)
    await db.commit()
    
    return {"success": True}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/me/photo", response_model=DocumentResponse)
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload profile photo.
    """
    file_location = f"{UPLOAD_DIR}/{current_user.id}_photo_{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Check if photo already exists and update or create new?
    # For now, append new record. Ideally invalidating old one.
    
    doc = Document(
        user_id=current_user.id,
        document_type="profile_photo",
        file_path=file_location,
        file_url=f"/static/{current_user.id}_photo_{file.filename}",
        status="approved" 
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@router.post("/me/documents", response_model=DocumentResponse)
@limiter.limit("10/minute")  # Max 10 document uploads per minute
async def upload_document(
    request: Request,
    document_type: str, 
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload driver documents (license, insurance, vehicle).
    """
    valid_types = ["license", "insurance", "vehicle"]
    if document_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid document type")

    file_location = f"{UPLOAD_DIR}/{current_user.id}_{document_type}_{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    doc = Document(
        user_id=current_user.id,
        document_type=document_type,
        file_path=file_location,
        file_url=f"/static/{current_user.id}_{document_type}_{file.filename}",
        status="pending"
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@router.get("/me/verification-status", response_model=Any)
async def get_verification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get driver verification status.
    Checks profile completion and document uploads.
    """
    # 1. Check Profile Completeness
    required_fields = ["full_name", "phone_number", "email", "car_model", "license_plate", "car_color"]
    missing_fields = []
    
    for field in required_fields:
        if not getattr(current_user, field):
             missing_fields.append(field)
             
    profile_complete = len(missing_fields) == 0

    # 2. Check Documents
    query = select(Document).where(Document.user_id == current_user.id)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    docs_status = {
        "license": False,
        "insurance": False,
        "vehicle": False,
        "profile_photo": False
    }
    
    # Check if approved or pending docs exist for each type
    for doc in documents:
        if doc.document_type in docs_status:
             # Consider uploaded if pending or approved
             if doc.status in ["approved", "pending"]:
                 docs_status[doc.document_type] = True

    # 3. Determine Overall Status
    verification_status = "incomplete"
    
    all_docs_uploaded = all([docs_status["license"], docs_status["insurance"], docs_status["vehicle"]])
    
    if profile_complete and all_docs_uploaded:
        verification_status = "pending"
        # Check if actually approved (all docs approved)
        approved_docs = True
        for doc in documents:
            if doc.document_type in ["license", "insurance", "vehicle"] and doc.status != "approved":
                approved_docs = False
                break
        if approved_docs and all_docs_uploaded:
             verification_status = "approved"

    return {
        "profile_complete": profile_complete,
        "missing_fields": missing_fields,
        "documents_uploaded": docs_status,
        "verification_status": verification_status
    }


@router.post("/me/verify-phone", status_code=status.HTTP_200_OK)
async def request_phone_verification(
    request: PhoneVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request SMS verification code.
    """
    return await verification_service.send_phone_verification_code(
        current_user.id,
        request.phone_number,
        db
    )

@router.post("/me/verify-phone/confirm", status_code=status.HTTP_200_OK)
async def confirm_phone_verification(
    request: PhoneVerificationConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Confirm SMS verification code.
    """
    return await verification_service.verify_phone_code(
        current_user.id,
        request.code,
        db
    )

@router.post("/me/verify-email", status_code=status.HTTP_200_OK)
async def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request email verification link.
    """
    return await verification_service.send_email_verification(current_user.id, db)

@router.post("/verify-email/confirm", status_code=status.HTTP_200_OK)
async def confirm_email_verification(
    token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Confirm email verification (token).
    Public endpoint.
    """
    return await verification_service.confirm_email_verification(token, db)

@router.post("/me/request-deletion", status_code=status.HTTP_200_OK)
async def request_account_deletion(
    request: AccountDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request account deletion.
    """
    return await profile_service.request_account_deletion(
        current_user.id,
        request,
        db
    )

@router.delete("/me/cancel-deletion", status_code=status.HTTP_200_OK)
async def cancel_account_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Cancel pending account deletion.
    """
    return await profile_service.cancel_account_deletion(current_user.id, db)
