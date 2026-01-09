"""
Email client for sending notifications via SendGrid.

For MVP, we use SendGrid's free tier (100 emails/day).
For production AWS deployment, migrate to AWS SES for cost efficiency.

Migration Guide:
- SendGrid: Easy setup, good for development/MVP
- AWS SES: Production-ready, $0.10/1000 emails, requires AWS account
"""
import logging
from typing import Optional
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

class EmailClient:
    """
    Email client supporting both SendGrid (MVP) and AWS SES (production).
    
    Current: SendGrid
    Future: AWS SES (when deploying to AWS)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: str = "noreply@sjsurideshare.com",
        from_name: str = "SJSU RideShare"
    ):
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email
        self.from_name = from_name
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not set - emails will be logged only")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)
    
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
        if not self.client:
            logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
            logger.debug(f"HTML Content: {html_content[:100]}...")
            return True
        
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

# Global instance
email_client = EmailClient()


# AWS SES Integration (For Future Use)
"""
When migrating to AWS SES:

1. Install boto3:
   pip install boto3

2. Configure AWS credentials:
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_REGION=us-west-2

3. Verify sender email in SES console

4. Replace send_email implementation:

import boto3
from botocore.exceptions import ClientError

class EmailClient:
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION'))
    
    async def send_email(self, to_email, subject, html_content, text_content=None):
        try:
            response = self.ses_client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Html': {'Data': html_content},
                        'Text': {'Data': text_content or ''}
                    }
                }
            )
            logger.info(f"Email sent via SES: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"SES error: {e}")
            return False

Benefits of AWS SES:
- Much cheaper: $0.10 per 1,000 emails (vs SendGrid $15/month for 40k)
- Integrated with AWS ecosystem
- High deliverability
- No daily limits on verified production account
"""
