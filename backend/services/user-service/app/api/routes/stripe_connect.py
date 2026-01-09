from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.stripe_connect_service import stripe_connect_service

router = APIRouter()

@router.post("/connect/onboard")
async def start_connect_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start Stripe Connect onboarding for driver.
    Generates an account link for the user to complete KYC.
    """
    if current_user.stripe_connect_id:
        # Check if already fully onboarded or just needs to resume
        status_info = await stripe_connect_service.get_account_status(current_user.stripe_connect_id)
        if status_info['charges_enabled'] and status_info['payouts_enabled']:
            return {"message": "Already onboarded", "account_id": current_user.stripe_connect_id}
            
        # Needs to resume/update - create new account link for existing account
        try:
            account_link = await stripe_connect_service.create_account_link(
                account_id=current_user.stripe_connect_id,
                refresh_url=f"{current_user.email}/connect/refresh",  # URL to redirect if link expires
                return_url=f"{current_user.email}/connect/return"     # URL after completion
            )
            return {
                "message": "Resume onboarding",
                "account_id": current_user.stripe_connect_id,
                "url": account_link['url']
            }
        except Exception as resume_error:
            # If resume fails, fall through to create new account
            pass

    try:
        result = await stripe_connect_service.create_connect_account(
            user_id=current_user.id,
            email=current_user.email
        )
        
        # Save account ID
        current_user.stripe_connect_id = result['account_id']
        db.add(current_user)
        await db.commit()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connect/dashboard")
async def get_dashboard_link(
    current_user: User = Depends(get_current_user)
):
    """
    Get link to Stripe Express Dashboard for payouts/tax docs.
    """
    if not current_user.stripe_connect_id:
        raise HTTPException(status_code=400, detail="No Connect account found")
        
    try:
        url = await stripe_connect_service.create_login_link(current_user.stripe_connect_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
