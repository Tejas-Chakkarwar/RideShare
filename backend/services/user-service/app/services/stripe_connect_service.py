import stripe
from uuid import UUID
import logging
from typing import Dict, Any

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class StripeConnectService:
    """Handle Stripe Connect for driver payouts"""
    
    async def create_connect_account(self, user_id: UUID, email: str) -> Dict[str, Any]:
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

    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
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
