# SJSU RideShare Development Guide
## Section 9: Stripe Payment Integration

**Version:** 1.0  
**Duration:** Week 9  
**Focus:** Secure payment processing, escrow, driver payouts, refunds

---

# SECTION 9: Stripe Payment Integration

## Learning Objectives
- Integrate Stripe for payment processing
- Implement escrow payment flow (hold → capture)
- Set up Stripe Connect for driver payouts
- Handle payment webhooks
- Process refunds based on cancellation policy
- Implement platform fees
- Secure payment handling
- PCI compliance

## Technologies
- Stripe API (Python SDK)
- Stripe Connect (marketplace payments)
- Stripe Webhooks (event handling)
- Stripe Payment Intents
- Stripe Customer Portal

## Prerequisites
- Sections 1-8 completed ✅
- Stripe account (free test mode)
- Understanding of payment flows
- Booking service operational
- SSL/HTTPS for webhooks

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Stripe Payment Integration

CONTEXT:
Sections 1-8 completed. Bookings working, tracking operational.
Integrating Stripe for secure payments with escrow and driver payouts.
Section 9 of 13.

GOAL:
Implement complete payment system:
- Charge passengers securely
- Hold funds in escrow until ride completion
- Transfer to drivers with platform fee
- Handle refunds per cancellation policy
- Stripe Connect for driver payouts
- Webhook handling for events

DETAILED REQUIREMENTS:

1. STRIPE SETUP (Manual Steps):

   A. Create Stripe Account:
   - Go to stripe.com
   - Sign up for account
   - Stay in TEST MODE for development
   
   B. Get API Keys:
   - Dashboard → Developers → API keys
   - Copy: Publishable key (pk_test_...)
   - Copy: Secret key (sk_test_...)
   - Store in .env (NEVER commit to Git)
   
   C. Enable Stripe Connect:
   - Dashboard → Connect → Get Started
   - Choose "Platform or marketplace"
   - Set up OAuth settings
   - Get Connect client ID
   
   D. Configure Webhooks:
   - Dashboard → Developers → Webhooks
   - Add endpoint: https://your-domain/api/v1/webhooks/stripe
   - Select events:
     * payment_intent.succeeded
     * payment_intent.payment_failed
     * account.updated
     * charge.refunded
   - Copy webhook secret (whsec_...)

2. UPDATE BOOKING MODEL:

   Add payment fields to Booking model (booking-service):
   ```python
   # Payment fields
   stripe_payment_intent_id = Column(String(100), nullable=True, unique=True)
   stripe_charge_id = Column(String(100), nullable=True)
   stripe_refund_id = Column(String(100), nullable=True)
   amount = Column(Numeric(10, 2), nullable=False)
   platform_fee = Column(Numeric(10, 2), nullable=False, default=0)
   driver_payout = Column(Numeric(10, 2), nullable=False, default=0)
   payment_status = Column(
       Enum('pending', 'authorized', 'succeeded', 'failed', 'refunded'),
       nullable=False,
       default='pending'
   )
   payment_method_id = Column(String(100), nullable=True)
   ```

3. UPDATE USER MODEL:

   Add Stripe fields to User model (user-service):
   ```python
   # Stripe fields
   stripe_customer_id = Column(String(100), nullable=True, unique=True, index=True)
   stripe_connect_id = Column(String(100), nullable=True, unique=True, index=True)
   stripe_account_verified = Column(Boolean, default=False)
   stripe_charges_enabled = Column(Boolean, default=False)
   stripe_payouts_enabled = Column(Boolean, default=False)
   ```

4. PAYMENT SERVICE (booking-service/app/services/payment_service.py):

   ```python
   import stripe
   from decimal import Decimal
   from uuid import UUID
   from sqlalchemy.ext.asyncio import AsyncSession
   from typing import Optional
   import logging
   
   from app.core.config import settings
   from app.models.booking import Booking
   from app.clients.user_client import user_client
   
   stripe.api_key = settings.STRIPE_SECRET_KEY
   logger = logging.getLogger(__name__)
   
   class PaymentService:
       """Handle all Stripe payment operations"""
       
       PLATFORM_FEE_PERCENTAGE = 0.10  # 10% platform fee
       
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
           
           if user.get('stripe_customer_id'):
               return user['stripe_customer_id']
           
           return await self.create_customer(user_id, user['email'])
       
       async def create_payment_intent(
           self,
           booking: Booking,
           customer_id: str,
           payment_method_id: Optional[str] = None
       ) -> dict:
           """
           Create Payment Intent (authorize but don't capture)
           
           Flow:
           1. Calculate amount and fees
           2. Create Payment Intent with capture_method='manual'
           3. This authorizes the card but doesn't charge
           4. Funds are held until capture or 7 days
           """
           try:
               # Calculate amounts
               total_amount = booking.amount
               platform_fee = total_amount * Decimal(str(self.PLATFORM_FEE_PERCENTAGE))
               driver_payout = total_amount - platform_fee
               
               # Convert to cents (Stripe uses smallest currency unit)
               amount_cents = int(total_amount * 100)
               
               # Create Payment Intent
               intent = stripe.PaymentIntent.create(
                   amount=amount_cents,
                   currency='usd',
                   customer=customer_id,
                   payment_method=payment_method_id,
                   confirmation_method='automatic',
                   capture_method='manual',  # Important: don't capture yet
                   confirm=True if payment_method_id else False,
                   metadata={
                       'booking_id': str(booking.id),
                       'ride_id': str(booking.ride_id),
                       'passenger_id': str(booking.passenger_id),
                       'platform_fee': str(platform_fee),
                       'driver_payout': str(driver_payout)
                   },
                   description=f"SJSU RideShare - Booking {booking.id}"
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
                   'amount': total_amount,
                   'platform_fee': platform_fee,
                   'driver_payout': driver_payout
               }
           
           except stripe.error.CardError as e:
               logger.error(f"Card error: {e.user_message}")
               raise Exception(f"Payment failed: {e.user_message}")
           except stripe.error.StripeError as e:
               logger.error(f"Stripe error: {e}")
               raise
       
       async def capture_payment(
           self,
           booking: Booking,
           driver_stripe_connect_id: str
       ) -> dict:
           """
           Capture payment after ride completion
           Transfer to driver with platform fee
           
           Called when ride is completed
           """
           try:
               if not booking.stripe_payment_intent_id:
                   raise Exception("No payment intent found")
               
               # Capture the payment
               intent = stripe.PaymentIntent.capture(
                   booking.stripe_payment_intent_id
               )
               
               # Calculate transfer amount (to driver)
               driver_amount_cents = int(booking.driver_payout * 100)
               
               # Transfer to driver (requires Stripe Connect)
               transfer = stripe.Transfer.create(
                   amount=driver_amount_cents,
                   currency='usd',
                   destination=driver_stripe_connect_id,
                   transfer_group=str(booking.id),
                   metadata={
                       'booking_id': str(booking.id),
                       'ride_id': str(booking.ride_id)
                   }
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
                   'amount_captured': booking.amount,
                   'driver_payout': booking.driver_payout,
                   'platform_fee': booking.platform_fee
               }
           
           except stripe.error.StripeError as e:
               logger.error(f"Error capturing payment: {e}")
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
               
               intent = stripe.PaymentIntent.cancel(
                   booking.stripe_payment_intent_id
               )
               
               booking.payment_status = 'cancelled'
               
               logger.info(f"Cancelled payment intent {intent.id}")
               
               return {
                   'status': 'cancelled',
                   'payment_intent_id': intent.id
               }
           
           except stripe.error.StripeError as e:
               logger.error(f"Error cancelling payment: {e}")
               raise
       
       async def create_refund(
           self,
           booking: Booking,
           refund_percentage: float = 1.0,
           reason: str = "requested_by_customer"
       ) -> dict:
           """
           Create refund for captured payment
           
           Args:
               booking: Booking to refund
               refund_percentage: 0.0 to 1.0 (1.0 = full refund)
               reason: 'requested_by_customer', 'duplicate', 'fraudulent'
           """
           try:
               if not booking.stripe_charge_id:
                   raise Exception("No charge found to refund")
               
               # Calculate refund amount
               refund_amount = booking.amount * Decimal(str(refund_percentage))
               refund_cents = int(refund_amount * 100)
               
               # Create refund
               refund = stripe.Refund.create(
                   charge=booking.stripe_charge_id,
                   amount=refund_cents,
                   reason=reason,
                   metadata={
                       'booking_id': str(booking.id),
                       'refund_percentage': refund_percentage
                   }
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
           cancellation_time
       ) -> float:
           """
           Calculate refund percentage based on cancellation policy
           
           Policy:
           - > 24 hours before: 100% refund
           - 2-24 hours before: 50% refund
           - < 2 hours before: 0% refund
           - Driver cancellation: Always 100% refund
           """
           from datetime import timedelta
           
           time_until_ride = booking.estimated_pickup_time - cancellation_time
           hours_until = time_until_ride.total_seconds() / 3600
           
           if hours_until >= 24:
               return 1.0  # 100%
           elif hours_until >= 2:
               return 0.5  # 50%
           else:
               return 0.0  # No refund
   
   payment_service = PaymentService()
   ```

5. STRIPE CONNECT FOR DRIVERS (user-service/app/services/stripe_connect_service.py):

   ```python
   import stripe
   from uuid import UUID
   import logging
   
   from app.core.config import settings
   
   stripe.api_key = settings.STRIPE_SECRET_KEY
   logger = logging.getLogger(__name__)
   
   class StripeConnectService:
       """Handle Stripe Connect for driver payouts"""
       
       async def create_connect_account(self, user_id: UUID, email: str) -> dict:
           """
           Create Stripe Connect account for driver
           Returns account_id and onboarding link
           """
           try:
               # Create Connect account
               account = stripe.Account.create(
                   type='express',  # Express account (easier onboarding)
                   country='US',
                   email=email,
                   capabilities={
                       'card_payments': {'requested': True},
                       'transfers': {'requested': True}
                   },
                   business_type='individual',
                   metadata={
                       'user_id': str(user_id),
                       'platform': 'sjsu_rideshare'
                   }
               )
               
               # Create account link for onboarding
               account_link = stripe.AccountLink.create(
                   account=account.id,
                   refresh_url=f"{settings.FRONTEND_URL}/driver/connect/refresh",
                   return_url=f"{settings.FRONTEND_URL}/driver/connect/success",
                   type='account_onboarding'
               )
               
               logger.info(f"Created Connect account {account.id} for user {user_id}")
               
               return {
                   'account_id': account.id,
                   'onboarding_url': account_link.url,
                   'expires_at': account_link.expires_at
               }
           
           except stripe.error.StripeError as e:
               logger.error(f"Error creating Connect account: {e}")
               raise
       
       async def get_account_status(self, account_id: str) -> dict:
           """
           Check Connect account verification status
           """
           try:
               account = stripe.Account.retrieve(account_id)
               
               return {
                   'account_id': account.id,
                   'charges_enabled': account.charges_enabled,
                   'payouts_enabled': account.payouts_enabled,
                   'requirements': {
                       'currently_due': account.requirements.currently_due,
                       'eventually_due': account.requirements.eventually_due,
                       'past_due': account.requirements.past_due
                   },
                   'verification_status': account.requirements.disabled_reason
               }
           
           except stripe.error.StripeError as e:
               logger.error(f"Error retrieving account: {e}")
               raise
       
       async def create_login_link(self, account_id: str) -> str:
           """
           Create login link for driver to access Stripe dashboard
           """
           try:
               login_link = stripe.Account.create_login_link(account_id)
               return login_link.url
           
           except stripe.error.StripeError as e:
               logger.error(f"Error creating login link: {e}")
               raise
   
   stripe_connect_service = StripeConnectService()
   ```

6. WEBHOOK HANDLER (booking-service/app/api/routes/webhooks.py):

   ```python
   from fastapi import APIRouter, Request, HTTPException, Header
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   import stripe
   import logging
   
   from app.core.config import settings
   from app.core.database import get_db
   from app.models.booking import Booking
   from app.services.notification_service import notification_service
   
   router = APIRouter()
   logger = logging.getLogger(__name__)
   
   stripe.api_key = settings.STRIPE_SECRET_KEY
   
   @router.post("/stripe")
   async def stripe_webhook(
       request: Request,
       stripe_signature: str = Header(None),
       db: AsyncSession = Depends(get_db)
   ):
       """
       Handle Stripe webhook events
       
       Security: Verify webhook signature
       """
       payload = await request.body()
       
       try:
           # Verify webhook signature
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
       
       # Handle the event
       event_type = event['type']
       
       if event_type == 'payment_intent.succeeded':
           payment_intent = event['data']['object']
           await handle_payment_succeeded(payment_intent, db)
       
       elif event_type == 'payment_intent.payment_failed':
           payment_intent = event['data']['object']
           await handle_payment_failed(payment_intent, db)
       
       elif event_type == 'account.updated':
           account = event['data']['object']
           await handle_account_updated(account)
       
       elif event_type == 'charge.refunded':
           charge = event['data']['object']
           await handle_charge_refunded(charge, db)
       
       else:
           logger.info(f"Unhandled event type: {event_type}")
       
       return {"status": "success"}
   
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
       await db.commit()
       
       # Send notification
       await notification_service.send_payment_confirmation(
           booking.passenger_id,
           {'booking_id': booking_id, 'amount': booking.amount}
       )
       
       logger.info(f"Payment succeeded for booking {booking_id}")
   
   async def handle_payment_failed(payment_intent: dict, db: AsyncSession):
       """Handle failed payment"""
       booking_id = payment_intent['metadata'].get('booking_id')
       
       if not booking_id:
           return
       
       result = await db.execute(
           select(Booking).where(Booking.id == booking_id)
       )
       booking = result.scalar_one_or_none()
       
       if booking:
           booking.payment_status = 'failed'
           await db.commit()
           
           await notification_service.send_payment_failed(
               booking.passenger_id,
               {'booking_id': booking_id}
           )
       
       logger.error(f"Payment failed for booking {booking_id}")
   
   async def handle_account_updated(account: dict):
       """Handle Connect account updates"""
       user_id = account['metadata'].get('user_id')
       
       if not user_id:
           return
       
       # Update user's Connect status
       await user_client.update_stripe_connect_status(
           user_id,
           {
               'charges_enabled': account['charges_enabled'],
               'payouts_enabled': account['payouts_enabled']
           }
       )
       
       logger.info(f"Updated Connect account for user {user_id}")
   
   async def handle_charge_refunded(charge: dict, db: AsyncSession):
       """Handle refund"""
       # Find booking by charge_id
       result = await db.execute(
           select(Booking).where(Booking.stripe_charge_id == charge['id'])
       )
       booking = result.scalar_one_or_none()
       
       if booking:
           booking.payment_status = 'refunded'
           await db.commit()
           
           await notification_service.send_refund_processed(
               booking.passenger_id,
               {'booking_id': str(booking.id), 'amount': booking.amount}
           )
       
       logger.info(f"Refund processed for charge {charge['id']}")
   ```

7. API ENDPOINTS (booking-service/app/api/routes/payments.py):

   ```python
   from fastapi import APIRouter, Depends, HTTPException
   from sqlalchemy.ext.asyncio import AsyncSession
   from uuid import UUID
   
   from app.core.database import get_db
   from app.services.payment_service import payment_service
   from app.services.booking_service import booking_service
   from app.schemas.payment import (
       PaymentMethodSchema,
       PaymentIntentResponse,
       RefundRequest
   )
   
   router = APIRouter()
   
   @router.post("/bookings/{booking_id}/payment-intent")
   async def create_payment_intent(
       booking_id: UUID,
       payment_method: PaymentMethodSchema,
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """
       Create payment intent for booking
       Called when booking is approved by driver
       """
       booking = await booking_service.get_booking(booking_id, db)
       
       if not booking:
           raise HTTPException(404, "Booking not found")
       
       if booking.passenger_id != current_user_id:
           raise HTTPException(403, "Not authorized")
       
       if booking.status != 'approved':
           raise HTTPException(400, "Booking not approved")
       
       # Get or create Stripe customer
       customer_id = await payment_service.get_or_create_customer(current_user_id)
       
       # Create payment intent
       result = await payment_service.create_payment_intent(
           booking,
           customer_id,
           payment_method.payment_method_id
       )
       
       await db.commit()
       
       return result
   
   @router.post("/bookings/{booking_id}/capture")
   async def capture_payment(
       booking_id: UUID,
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """
       Capture payment after ride completion
       Called by driver when marking ride as complete
       """
       booking = await booking_service.get_booking(booking_id, db)
       
       if not booking:
           raise HTTPException(404, "Booking not found")
       
       # Verify driver
       ride = await ride_client.get_ride(booking.ride_id)
       if ride['driver_id'] != current_user_id:
           raise HTTPException(403, "Not authorized")
       
       if booking.status != 'completed':
           raise HTTPException(400, "Booking not completed")
       
       # Get driver's Connect account
       driver = await user_client.get_user(current_user_id)
       if not driver.get('stripe_connect_id'):
           raise HTTPException(400, "Driver hasn't set up payouts")
       
       # Capture payment
       result = await payment_service.capture_payment(
           booking,
           driver['stripe_connect_id']
       )
       
       await db.commit()
       
       return result
   
   @router.post("/bookings/{booking_id}/refund")
   async def refund_payment(
       booking_id: UUID,
       refund_request: RefundRequest,
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """
       Process refund for cancelled booking
       """
       booking = await booking_service.get_booking(booking_id, db)
       
       if not booking:
           raise HTTPException(404, "Booking not found")
       
       # Calculate refund percentage
       refund_percentage = await payment_service.calculate_refund_amount(
           booking,
           datetime.utcnow()
       )
       
       # Process refund
       result = await payment_service.create_refund(
           booking,
           refund_percentage,
           refund_request.reason
       )
       
       await db.commit()
       
       return result
   ```

8. DRIVER CONNECT ENDPOINTS (user-service/app/api/routes/stripe_connect.py):

   ```python
   from fastapi import APIRouter, Depends
   from uuid import UUID
   
   from app.services.stripe_connect_service import stripe_connect_service
   
   router = APIRouter()
   
   @router.post("/connect/onboard")
   async def start_connect_onboarding(
       current_user_id: UUID = Depends(get_current_user_id)
   ):
       """
       Start Stripe Connect onboarding for driver
       Returns onboarding URL
       """
       user = await get_user(current_user_id)
       
       if not user.driver_license_verified:
           raise HTTPException(400, "Verify driver license first")
       
       result = await stripe_connect_service.create_connect_account(
           current_user_id,
           user.email
       )
       
       # Save account_id to user
       user.stripe_connect_id = result['account_id']
       await db.commit()
       
       return result
   
   @router.get("/connect/status")
   async def get_connect_status(
       current_user_id: UUID = Depends(get_current_user_id)
   ):
       """Get driver's Connect account status"""
       user = await get_user(current_user_id)
       
       if not user.stripe_connect_id:
           return {"status": "not_connected"}
       
       status = await stripe_connect_service.get_account_status(
           user.stripe_connect_id
       )
       
       return status
   
   @router.get("/connect/dashboard")
   async def get_dashboard_link(
       current_user_id: UUID = Depends(get_current_user_id)
   ):
       """Get link to Stripe dashboard"""
       user = await get_user(current_user_id)
       
       if not user.stripe_connect_id:
           raise HTTPException(400, "Not connected to Stripe")
       
       url = await stripe_connect_service.create_login_link(
           user.stripe_connect_id
       )
       
       return {"dashboard_url": url}
   ```

9. PAYMENT FLOW SUMMARY:

   **A. Booking Creation → Approval:**
   1. Passenger requests booking
   2. Driver approves booking
   3. Frontend calls POST /bookings/{id}/payment-intent
   4. Creates Payment Intent (holds funds)
   5. Booking status: payment_status = 'authorized'
   
   **B. Ride Completion → Payout:**
   1. Driver completes ride
   2. Driver calls POST /bookings/{id}/capture
   3. Captures payment (charges customer)
   4. Transfers to driver (minus platform fee)
   5. Booking status: payment_status = 'succeeded'
   
   **C. Cancellation → Refund:**
   1. Passenger/driver cancels
   2. System calculates refund % based on time
   3. If not captured: cancel Payment Intent
   4. If captured: create Refund
   5. Booking status: payment_status = 'refunded'

10. TESTING WITH TEST CARDS:

    Test Card Numbers (Stripe Test Mode):
    ```
    Success: 4242 4242 4242 4242
    Decline: 4000 0000 0000 0002
    Insufficient funds: 4000 0000 0000 9995
    Requires authentication: 4000 0027 6000 3184
    
    CVC: Any 3 digits
    Expiry: Any future date
    ```

11. ENVIRONMENT VARIABLES:

    ```
    # Stripe
    STRIPE_SECRET_KEY=sk_test_...
    STRIPE_PUBLISHABLE_KEY=pk_test_...
    STRIPE_WEBHOOK_SECRET=whsec_...
    STRIPE_CONNECT_CLIENT_ID=ca_...
    ```

12. GENERATE LEARNING DOCUMENTATION:

    Create: docs/learning/09-payment-processing.md
    
    Cover (20+ pages):
    1. Payment Processing Fundamentals
    2. Stripe Architecture
    3. Payment Intents vs Charges
    4. Escrow Pattern (authorize → capture)
    5. Stripe Connect for Marketplaces
    6. Platform Fees and Payouts
    7. Refunds and Disputes
    8. Webhooks and Event Handling
    9. PCI Compliance
    10. Testing Payments
    11. Security Best Practices
    12. Common Pitfalls

13. TESTING (tests/test_payments.py):

    ```python
    - test_create_stripe_customer
    - test_create_payment_intent
    - test_capture_payment
    - test_cancel_payment_intent
    - test_create_refund_full
    - test_create_refund_partial
    - test_calculate_refund_percentage
    - test_stripe_connect_onboarding
    - test_webhook_payment_succeeded
    - test_webhook_payment_failed
    - test_webhook_signature_validation
    ```

CRITICAL REQUIREMENTS:

Security:
- NEVER expose secret keys
- Verify webhook signatures
- Use HTTPS for webhooks
- Validate all amounts server-side
- Never trust client-side calculations

PCI Compliance:
- Never store card numbers
- Use Stripe.js for card collection
- All card data goes directly to Stripe
- Use tokens/payment_methods only

Error Handling:
- Handle all Stripe exceptions
- Retry failed webhooks
- Log all payment events
- Alert on payment failures

Testing:
- Use test mode extensively
- Test all card scenarios
- Test webhook events
- Never use real cards in development

VERIFICATION CHECKLIST:
- [ ] Stripe account created (test mode)
- [ ] API keys configured
- [ ] Webhook endpoint working
- [ ] Webhook signature verified
- [ ] Can create customer
- [ ] Can create payment intent
- [ ] Payment intent shows in Stripe dashboard
- [ ] Can capture payment
- [ ] Platform fee calculated correctly
- [ ] Driver receives payout
- [ ] Can cancel payment intent
- [ ] Can create refund
- [ ] Refund policy working (24h, 2h rules)
- [ ] Connect onboarding works
- [ ] Connect account status updates
- [ ] Dashboard link works
- [ ] Webhooks received
- [ ] All webhook events handled
- [ ] Test cards work
- [ ] All tests pass
- [ ] No secrets in code

Please generate payment service with comprehensive Stripe integration.
```

---

## TESTING CHECKLIST - SECTION 9

### Stripe Setup
- [ ] Account created
- [ ] Test mode enabled
- [ ] API keys copied
- [ ] Keys in .env file
- [ ] Webhook endpoint created
- [ ] Webhook secret copied
- [ ] Connect enabled

### Customer Creation
Test: Create new user, then:
```python
POST /api/v1/payments/customer
```
- [ ] Stripe customer created
- [ ] customer_id stored in database
- [ ] Visible in Stripe dashboard

### Payment Intent (Authorization)
Test: Approve a booking, then:
```python
POST /api/v1/payments/bookings/{id}/payment-intent
{
  "payment_method_id": "pm_card_visa"
}
```
- [ ] Payment intent created
- [ ] Status: requires_capture
- [ ] Funds authorized (not charged)
- [ ] Visible in Stripe dashboard
- [ ] Amount correct
- [ ] Metadata includes booking_id

### Payment Capture
Test: Complete ride, then:
```python
POST /api/v1/payments/bookings/{id}/capture
```
- [ ] Payment captured
- [ ] Customer charged
- [ ] Transfer created to driver
- [ ] Platform fee deducted (10%)
- [ ] Driver receives correct amount
- [ ] Booking payment_status = 'succeeded'

### Refunds - Full (> 24 hours)
Scenario: Cancel 25 hours before ride
```python
POST /api/v1/payments/bookings/{id}/refund
```
- [ ] 100% refund calculated
- [ ] Refund processed
- [ ] Refund visible in dashboard
- [ ] Booking payment_status = 'refunded'

### Refunds - Partial (2-24 hours)
Scenario: Cancel 12 hours before ride
- [ ] 50% refund calculated
- [ ] Partial refund processed
- [ ] Correct amount refunded

### Refunds - None (< 2 hours)
Scenario: Cancel 1 hour before ride
- [ ] 0% refund calculated
- [ ] No refund processed
- [ ] Passenger notified

### Cancel Payment Intent
Scenario: Cancel before capture
```python
POST /api/v1/payments/bookings/{id}/cancel-payment
```
- [ ] Payment intent cancelled
- [ ] Hold released
- [ ] No charge to customer

### Stripe Connect - Onboarding
Test: Driver starts onboarding
```python
POST /api/v1/users/connect/onboard
```
- [ ] Connect account created
- [ ] Onboarding URL returned
- [ ] Opens Stripe onboarding
- [ ] Can complete identity verification
- [ ] Can add bank account

### Stripe Connect - Status
```python
GET /api/v1/users/connect/status
```
- [ ] Returns account status
- [ ] Shows charges_enabled
- [ ] Shows payouts_enabled
- [ ] Shows requirements (if any)

### Stripe Connect - Dashboard
```python
GET /api/v1/users/connect/dashboard
```
- [ ] Returns dashboard URL
- [ ] Opens Stripe Express dashboard
- [ ] Driver can see transactions

### Webhooks - Payment Succeeded
Trigger: Capture a payment
- [ ] Webhook received
- [ ] Signature verified
- [ ] Booking updated
- [ ] Notification sent

### Webhooks - Payment Failed
Trigger: Use decline card (4000 0000 0000 0002)
- [ ] Webhook received
- [ ] Booking marked as failed
- [ ] Passenger notified

### Webhooks - Account Updated
Trigger: Complete Connect onboarding
- [ ] Webhook received
- [ ] User account updated
- [ ] charges_enabled updated
- [ ] payouts_enabled updated

### Webhooks - Charge Refunded
Trigger: Issue refund
- [ ] Webhook received
- [ ] Booking updated
- [ ] Passenger notified

### Test Cards
Using test card: 4242 4242 4242 4242
- [ ] Payment succeeds

Using test card: 4000 0000 0000 0002
- [ ] Payment declined
- [ ] Error message shown

### Amount Calculations
Booking: $30 total (3 seats × $10)
- [ ] Total: $30.00
- [ ] Platform fee (10%): $3.00
- [ ] Driver payout: $27.00
- [ ] Amounts match in Stripe

### Security
- [ ] No API keys in code
- [ ] Keys in .env only
- [ ] Webhook signature verified
- [ ] Invalid signature rejected (403)
- [ ] HTTPS used for webhooks
- [ ] Server-side validation only

### Error Handling
- [ ] Invalid card handled
- [ ] Insufficient funds handled
- [ ] Network errors handled
- [ ] Stripe API errors logged
- [ ] User-friendly error messages

### Integration
- [ ] Works with booking service
- [ ] Works with user service
- [ ] Notifications triggered
- [ ] Database transactions atomic

### Performance
- [ ] Payment intent < 2 seconds
- [ ] Capture < 2 seconds
- [ ] Webhook processing < 1 second

### Learning
- [ ] Read 09-payment-processing.md
- [ ] Understand Payment Intents
- [ ] Understand escrow pattern
- [ ] Understand Stripe Connect
- [ ] Understand webhooks
- [ ] PCI compliance understood

### Completion
- [ ] All tests passing
- [ ] Can process payments end-to-end
- [ ] Refunds working correctly
- [ ] Connect onboarding complete
- [ ] Webhooks functioning
- [ ] Ready for Section 10

---

**Date Completed:** _______________  
**Test Payments Made:** _____  
**Successful Captures:** _____  
**Refunds Processed:** _____  
**Notes:** _______________
