"""
Email Service

Handles email sending via SendGrid.
Supports templated emails using Jinja2.
"""
import logging
import sys
import os
from typing import Optional

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from shared.utils.email_client import EmailClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid"""

    def __init__(self):
        self.client = EmailClient(
            api_key=settings.SENDGRID_API_KEY,
            from_email=settings.SENDGRID_FROM_EMAIL,
            from_name=settings.SENDGRID_FROM_NAME
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        return await self.client.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def send_templated_email(
        self,
        to_email: str,
        subject: str,
        template_content: str
    ) -> bool:
        """
        Send email using pre-rendered template.

        Args:
            to_email: Recipient email address
            subject: Email subject
            template_content: Pre-rendered HTML template

        Returns:
            True if sent successfully, False otherwise
        """
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=template_content
        )


# Global instance
email_service = EmailService()
