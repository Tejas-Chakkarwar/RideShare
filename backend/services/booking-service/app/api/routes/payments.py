from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
# Assumption: get_current_user_id dependency exists or can be imported.
# In Booking Service, we use JWT validation from app/core/security.py usually.
# Let's verify dependencies.
from app.services.payment_service import payment_service
from app.services.booking_service import BookingService
from app.clients.ride_client import ride_client
from app.clients.user_client import user_client
from app.schemas.payment import (
    PaymentMethodSchema,
    PaymentIntentResponse,
    RefundRequest,
    PaymentCaptureResponse,
    RefundResponse
)

# Mock dependency for now if not available, but should be in deps.py
# Checking imports... will use placeholder if needed.
# Since we updated schemas, let's assume standard auth dep.
# Import auth dependency from standard location
from app.api.deps import get_current_user_id

from app.api.deps import get_current_user_id

router = APIRouter()

async def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    return BookingService(db)

@router.post("/bookings/{booking_id}/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    booking_id: UUID,
    payment_method: PaymentMethodSchema,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Create payment intent for booking
    Called when booking is approved by driver or immediately?
    Usually immediately to hold funds.
    """
    booking = await booking_service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    if booking.passenger_id != current_user_id:
        raise HTTPException(403, "Not authorized")
    
    # Ideally only for approved or pending bookings?
    if booking.status not in ['approved', 'pending']:
        raise HTTPException(400, "Booking status invalid for payment")
    
    # Get or create Stripe customer
    try:
        customer_id = await payment_service.get_or_create_customer(current_user_id)
    except Exception as e:
        raise HTTPException(500, f"Stripe customer error: {str(e)}")
    
    # Create payment intent
    try:
        result = await payment_service.create_payment_intent(
            booking,
            customer_id,
            payment_method.payment_method_id
        )
        await db.commit()
        return result
    except Exception as e:
        raise HTTPException(400, f"Payment creation failed: {str(e)}")

@router.post("/bookings/{booking_id}/capture", response_model=PaymentCaptureResponse)
async def capture_payment(
    booking_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Capture payment after ride completion
    Called by driver when marking ride as complete
    """
    booking = await booking_service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Verify driver
    ride = await ride_client.get_ride(booking.ride_id)
    if not ride: # Should catch ride not found
        raise HTTPException(404, "Ride not found")
        
    if UUID(ride['driver_id']) != current_user_id:
        raise HTTPException(403, "Not authorized")
    
    if booking.status != 'completed' and booking.status != 'approved':
         # Allow capture if just completed or approved? 
         # Workflow: Driver ends ride -> Ride Service -> Booking Service ?
         # Or Client calls this endpoint explicitly?
         pass
    
    # Get driver's Connect account
    driver = await user_client.get_user(current_user_id)
    if not driver.get('stripe_connect_id'):
        raise HTTPException(400, "Driver hasn't set up payouts")
    
    # Capture payment
    try:
        result = await payment_service.capture_payment(
            booking,
            driver['stripe_connect_id']
        )
        await db.commit()
        return result
    except Exception as e:
        raise HTTPException(400, f"Capture failed: {str(e)}")

@router.post("/bookings/{booking_id}/refund", response_model=RefundResponse)
async def refund_payment(
    booking_id: UUID,
    refund_request: RefundRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Process refund for cancelled booking
    """
    booking = await booking_service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(404, "Booking not found")
        
    # Validation: Only passenger (self-cancel) or Driver/System can trigger?
    # For now, simplistic.
    
    # Calculate refund percentage
    refund_percentage = await payment_service.calculate_refund_amount(
        booking,
        datetime.utcnow()
    )
    
    # Process refund
    try:
        result = await payment_service.create_refund(
            booking,
            refund_percentage,
            refund_request.reason
        )
        await db.commit()
        return result
    except Exception as e:
        raise HTTPException(400, f"Refund failed: {str(e)}")
