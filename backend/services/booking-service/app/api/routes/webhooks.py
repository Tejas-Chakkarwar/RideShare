from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe
import logging

from app.core.config import settings
from app.core.database import get_db
from app.models.booking import Booking
from app.clients.notification_client import notification_client

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

async def handle_payment_succeeded(payment_intent: dict, db: AsyncSession):
    """Handle successful payment"""
    booking_id = payment_intent['metadata'].get('booking_id')
    
    if not booking_id:
        logger.warning("Payment succeeded but no booking_id in metadata")
        return
    
    # Get booking
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        logger.error(f"Booking {booking_id} not found")
        return
    
    # Update status
    booking.payment_status = 'succeeded'
    booking.payment_method_id = payment_intent.get('payment_method')
    await db.commit()
    
    # Send notification
    await notification_service_send_confirmation(booking.passenger_id, booking_id, booking.total_amount)
    
    logger.info(f"Payment succeeded for booking {booking_id}")

async def handle_payment_failed(payment_intent: dict, db: AsyncSession):
    """Handle failed payment"""
    booking_id = payment_intent['metadata'].get('booking_id')
    
    if not booking_id:
        return
    
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if booking:
        booking.payment_status = 'failed'
        await db.commit()
        # Notify
    
    logger.error(f"Payment failed for booking {booking_id}")

async def handle_charge_refunded(charge: dict, db: AsyncSession):
    """Handle refund"""
    result = await db.execute(select(Booking).where(Booking.stripe_charge_id == charge['id']))
    booking = result.scalar_one_or_none()
    
    if booking:
        booking.payment_status = 'refunded'
        booking.stripe_refund_id = charge.get('refunds', {}).get('data', [{}])[0].get('id')
        await db.commit()
    
    logger.info(f"Refund processed for charge {charge['id']}")

async def notification_service_send_confirmation(passenger_id, booking_id, amount):
    """
    Send payment confirmation via Notification Service
    """
    try:
        await notification_client.send_payment_confirmation(
            passenger_id=passenger_id,
            booking_id=booking_id,
            amount=float(amount)
        )
    except Exception as e:
        logger.error(f"Failed to send payment notification: {e}")

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_type = event['type']
    
    if event_type == 'payment_intent.succeeded':
        try:
            await handle_payment_succeeded(event['data']['object'], db)
        except Exception as e:
            logger.error(f"Error handling payment_succeeded: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")
    
    elif event_type == 'payment_intent.payment_failed':
        try:
            await handle_payment_failed(event['data']['object'], db)
        except Exception as e:
            logger.error(f"Error handling payment_failed: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    elif event_type == 'charge.refunded':
        try:
            await handle_charge_refunded(event['data']['object'], db)
        except Exception as e:
            logger.error(f"Error handling charge_refunded: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    return {"status": "success"}
