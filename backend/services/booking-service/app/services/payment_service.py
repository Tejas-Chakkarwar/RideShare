import stripe
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
import logging
from app.utils.retry import retry

from app.core.config import settings
from app.models.booking import Booking
from app.clients.user_client import user_client

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class PaymentService:
    """Handle all Stripe payment operations"""
    
    PLATFORM_FEE_PERCENTAGE = 0.10  # 10% platform fee
    
    @retry(max_retries=3, exceptions=(stripe.error.APIConnectionError, stripe.error.RateLimitError))
    async def create_customer(self, user_id: UUID, email: str) -> str:
        """
        Create Stripe customer for user
        Returns customer_id
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                metadata={
                    'user_id': str(user_id),
                    'platform': 'sjsu_rideshare'
                }
            )
            
            # Update user with customer_id
            await user_client.update_stripe_customer_id(user_id, customer.id)
            
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise
    
    async def get_or_create_customer(self, user_id: UUID) -> str:
        """Get existing customer_id or create new one"""
        user = await user_client.get_user(user_id)
        
        if not user:
             raise ValueError(f"User {user_id} not found")

        if user.get('stripe_customer_id'):
            return user['stripe_customer_id']
        
        return await self.create_customer(user_id, user['email'])
    
    @retry(max_retries=3, exceptions=(stripe.error.APIConnectionError, stripe.error.RateLimitError))
    async def create_payment_intent(
        self,
        booking: Booking,
        customer_id: str,
        payment_method_id: Optional[str] = None
    ) -> dict:
        """
        Create Payment Intent (authorize but don't capture)
        """
        try:
            # Calculate amounts
            total_amount = booking.total_amount
            platform_fee = float(total_amount) * self.PLATFORM_FEE_PERCENTAGE
            driver_payout = float(total_amount) - platform_fee
            
            # Convert to cents (Stripe uses smallest currency unit)
            amount_cents = int(float(total_amount) * 100)
            
            # Create Payment Intent with Idempotency Key
            # Use booking_id as part of key to prevent duplicates for same booking
            idempotency_key = f"pi_{booking.id}_{amount_cents}"
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=customer_id,
                payment_method=payment_method_id,
                confirmation_method='automatic',
                capture_method='manual',
                confirm=True if payment_method_id else False,
                metadata={
                    'booking_id': str(booking.id),
                    'ride_id': str(booking.ride_id),
                    'passenger_id': str(booking.passenger_id),
                    'platform_fee': str(platform_fee),
                    'driver_payout': str(driver_payout)
                },
                description=f"SJSU RideShare - Booking {booking.id}",
                idempotency_key=idempotency_key
            )
            
            # Update booking
            booking.stripe_payment_intent_id = intent.id
            booking.payment_status = 'authorized'
            booking.platform_fee = platform_fee
            booking.driver_payout = driver_payout
            booking.payment_method_id = payment_method_id
            
            logger.info(f"Created Payment Intent {intent.id} for booking {booking.id}")
            
            return {
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
                'amount': float(total_amount),
                'platform_fee': platform_fee,
                'driver_payout': driver_payout
            }
        
        except stripe.error.CardError as e:
            logger.error(f"Card error: {e.user_message}")
            raise Exception(f"Payment failed: {e.user_message}")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise
    
    @retry(max_retries=3, exceptions=(stripe.error.APIConnectionError, stripe.error.RateLimitError))
    async def capture_payment(
        self,
        booking: Booking,
        driver_stripe_connect_id: str
    ) -> dict:
        """
        Capture payment after ride completion
        Transfer to driver with platform fee
        """
        try:
            if not booking.stripe_payment_intent_id:
                raise Exception("No payment intent found")
            
            # Idempotency key for capture
            idempotency_key = f"cap_{booking.id}"
            
            # Capture the payment
            intent = stripe.PaymentIntent.capture(
                booking.stripe_payment_intent_id,
                idempotency_key=idempotency_key
            )
            
            # Calculate transfer amount (to driver)
            driver_amount_cents = int(float(booking.driver_payout) * 100)
            
            # Transfer to driver (requires Stripe Connect)
            transfer_idempotency_key = f"tr_{booking.id}"
            transfer = stripe.Transfer.create(
                amount=driver_amount_cents,
                currency='usd',
                destination=driver_stripe_connect_id,
                transfer_group=str(booking.id),
                metadata={
                    'booking_id': str(booking.id),
                    'ride_id': str(booking.ride_id)
                },
                idempotency_key=transfer_idempotency_key
            )
            
            # Update booking
            booking.payment_status = 'succeeded'
            booking.stripe_charge_id = intent.latest_charge
            
            logger.info(
                f"Captured payment {intent.id} and transferred "
                f"${booking.driver_payout} to driver"
            )
            
            return {
                'status': 'succeeded',
                'charge_id': intent.latest_charge,
                'transfer_id': transfer.id,
                'amount_captured': float(booking.total_amount),
                'driver_payout': float(booking.driver_payout),
                'platform_fee': float(booking.platform_fee)
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Error capturing payment: {e}")
            # Don't set failed immediately if it's a temporary error, but for now:
            if not isinstance(e, stripe.error.RateLimitError):
                booking.payment_status = 'failed'
            raise
    
    async def cancel_payment(self, booking: Booking) -> dict:
        """
        Cancel payment intent (if not captured)
        This releases the hold on customer's card
        """
        try:
            if not booking.stripe_payment_intent_id:
                return {'status': 'no_payment'}
            
            idempotency_key = f"can_{booking.id}"
            intent = stripe.PaymentIntent.cancel(
                booking.stripe_payment_intent_id,
                idempotency_key=idempotency_key
            )
            
            booking.payment_status = 'cancelled'
            
            logger.info(f"Cancelled payment intent {intent.id}")
            
            return {
                'status': 'cancelled',
                'payment_intent_id': intent.id
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling payment: {e}")
            if "No such payment_intent" in str(e):
                return {'status': 'not_found'}
            raise
    
    async def create_refund(
        self,
        booking: Booking,
        refund_percentage: float = 1.0,
        reason: str = "requested_by_customer"
    ) -> dict:
        """
        Create refund for captured payment
        """
        try:
            if not booking.stripe_charge_id:
                 # If authorized but not captured, we should cancel instead
                 if booking.payment_status == 'authorized':
                     return await self.cancel_payment(booking)
                 raise Exception("No charge found to refund")
            
            # Calculate refund amount
            refund_amount = float(booking.total_amount) * refund_percentage
            refund_cents = int(refund_amount * 100)
            
            idempotency_key = f"ref_{booking.id}_{refund_cents}"
            
            # Create refund
            refund = stripe.Refund.create(
                charge=booking.stripe_charge_id,
                amount=refund_cents,
                reason=reason,
                metadata={
                    'booking_id': str(booking.id),
                    'refund_percentage': refund_percentage
                },
                idempotency_key=idempotency_key
            )
            
            booking.payment_status = 'refunded'
            booking.stripe_refund_id = refund.id
            
            logger.info(
                f"Created refund {refund.id} for ${refund_amount} "
                f"({refund_percentage * 100}%)"
            )
            
            return {
                'status': 'refunded',
                'refund_id': refund.id,
                'amount_refunded': refund_amount,
                'percentage': refund_percentage
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {e}")
            raise
    
    async def calculate_refund_amount(
        self,
        booking: Booking,
        cancellation_time: datetime
    ) -> float:
        """
        Calculate refund percentage based on cancellation policy:
        - > 24 hours before pickup: 100% refund
        - < 24 hours but > 1 hour before: 50% refund
        - < 1 hour before: 0% refund (charged full amount)
        """
        if not booking.pickup_time:
             # If no pickup time, assume full refund (safest default)
             return 1.0

        # Ensure cancellation_time is comparable to pickup_time (tz-aware/naive)
        # Using naive UTC for simplicity if DB stores naive UTC
        time_until_pickup = booking.pickup_time - cancellation_time
        hours_until_pickup = time_until_pickup.total_seconds() / 3600
        
        if hours_until_pickup >= 24:
            return 1.0
        elif hours_until_pickup >= 1:
            return 0.5
        else:
            return 0.0

payment_service = PaymentService()
