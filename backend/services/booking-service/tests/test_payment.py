import sys
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, ANY
from uuid import uuid4
from decimal import Decimal

# Mock Stripe Module and Exceptions
mock_stripe_module = MagicMock()
class MockStripeError(Exception): pass
class MockCardError(MockStripeError): 
    def __init__(self, message, *args, **kwargs):
        self.user_message = message
        super().__init__(message)

mock_stripe_module.error.StripeError = MockStripeError
mock_stripe_module.error.CardError = MockCardError
sys.modules['stripe'] = mock_stripe_module

# Mock asyncpg and database
sys.modules['asyncpg'] = MagicMock()
# We also need to mock sqlalchemy.ext.asyncio if it fails?
# Let's hope mocking asyncpg is enough if sqlalchemy checks for it.
# Actually, the error trace showed sqlalchemy importing asyncpg.

# Mock app.core.config
# sys.modules['app.core.config'] = MagicMock() # No, we need settings?
# Let's just mock the DB connection part.

from app.services.payment_service import payment_service
# Redefine Booking to avoid importing real Base
class Booking:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.stripe_payment_intent_id = kwargs.get('stripe_payment_intent_id')
        self.payment_status = kwargs.get('payment_status', 'pending')
        self.platform_fee = kwargs.get('platform_fee', 0)
        self.driver_payout = kwargs.get('driver_payout', 0)
        self.stripe_charge_id = kwargs.get('stripe_charge_id')
        self.pickup_location = kwargs.get('pickup_location')
        self.total_amount = kwargs.get('total_amount', 0)

# Patch app.models.booking.Booking with our MockBooking
# But payment_service imports it. We need to patch it BEFORE import?
# We already imported payment_service. It has reference to the REAL Booking class (constructor).
# No, it uses type hint `booking: Booking`. Python type hints don't enforce class identity at runtime unless checked.
# Code usages:
# booking.stripe_payment_intent_id = ...
# This works on any object with that attribute.
# So we can pass our MockBooking instance to the service methods!

# Mock Stripe (Fixture to reset/configure mocks)
import asyncio

@pytest.fixture
def mock_stripe():
    return mock_stripe_module

# Mock User Client
@pytest.fixture
def mock_user_client():
    with patch("app.services.payment_service.user_client") as mock:
        yield mock

def test_create_customer(mock_stripe, mock_user_client):
    async def _test():
        user_id = uuid4()
        email = "test@example.com"
        
        mock_stripe.Customer.create.return_value.id = "cus_123"
        mock_user_client.update_stripe_customer_id = AsyncMock()
        
        customer_id = await payment_service.create_customer(user_id, email)
        
        assert customer_id == "cus_123"
        mock_stripe.Customer.create.assert_called_once()
        mock_user_client.update_stripe_customer_id.assert_called_once_with(user_id, "cus_123")
    
    asyncio.run(_test())

def test_create_payment_intent(mock_stripe):
    async def _test():
        booking = Booking(
            id=uuid4(),
            ride_id=uuid4(),
            passenger_id=uuid4(),
            total_amount=Decimal("100.00")
        )
        customer_id = "cus_123"
        pm_id = "pm_123"
        
        mock_intent = MagicMock()
        mock_intent.id = "pi_123"
        mock_intent.client_secret = "secret"
        mock_intent.status = "requires_capture"
        mock_stripe.PaymentIntent.create.return_value = mock_intent
        
        result = await payment_service.create_payment_intent(booking, customer_id, pm_id)
        
        assert result['payment_intent_id'] == "pi_123"
        assert booking.stripe_payment_intent_id == "pi_123"
        assert booking.payment_status == "authorized"
        
        # Check fee calculation
        # 100 * 0.10 = 10.00
        assert booking.platform_fee == 10.00
        assert booking.driver_payout == 90.00
    
    asyncio.run(_test())

def test_capture_payment(mock_stripe):
    async def _test():
        booking = Booking(
            id=uuid4(),
            ride_id=uuid4(),
            stripe_payment_intent_id="pi_123",
            driver_payout=Decimal("90.00"),
            total_amount=Decimal("100.00"),
            platform_fee=Decimal("10.00")
        )
        driver_connect_id = "acct_123"
        
        mock_intent = MagicMock()
        mock_intent.latest_charge = "ch_123"
        mock_stripe.PaymentIntent.capture.return_value = mock_intent
        
        mock_transfer = MagicMock()
        mock_transfer.id = "tr_123"
        mock_stripe.Transfer.create.return_value = mock_transfer
        
        result = await payment_service.capture_payment(booking, driver_connect_id)
        
        assert result['status'] == "succeeded"
        assert booking.payment_status == "succeeded"
        
        # Verify Transfer call
        mock_stripe.Transfer.create.assert_called_once_with(
            amount=9000, # 90.00 * 100
            currency='usd',
            destination=driver_connect_id,
            transfer_group=str(booking.id),
            metadata={'booking_id': str(booking.id), 'ride_id': str(booking.ride_id)},
            idempotency_key=ANY
        )
    
    asyncio.run(_test())
