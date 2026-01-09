"""
Push Notification Service

Handles push notifications via Firebase Cloud Messaging (FCM).
Supports sending to individual devices and user groups.
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID
import os

logger = logging.getLogger(__name__)

# Firebase imports (optional - only if configured)
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase Admin SDK not installed. Push notifications disabled.")

from app.core.config import settings


class PushService:
    """Service for sending push notifications via Firebase"""

    def __init__(self):
        self.enabled = False
        self.app = None

        if not FIREBASE_AVAILABLE:
            logger.info("Firebase not available - push notifications disabled")
            return

        if not settings.FIREBASE_CREDENTIALS_PATH:
            logger.info("FIREBASE_CREDENTIALS_PATH not set - push notifications disabled")
            return

        if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            logger.warning(f"Firebase credentials file not found at {settings.FIREBASE_CREDENTIALS_PATH}")
            return

        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            self.app = firebase_admin.initialize_app(cred)
            self.enabled = True
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.enabled = False

    async def send_push(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send push notification to a specific device.

        Args:
            fcm_token: Firebase Cloud Messaging token
            title: Notification title
            body: Notification body
            data: Additional data for deep linking (must be string values)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"[MOCK PUSH] Title: {title}, Body: {body}")
            return True

        if not fcm_token:
            logger.warning("No FCM token provided")
            return False

        try:
            # Convert data values to strings (FCM requirement)
            string_data = {}
            if data:
                string_data = {k: str(v) for k, v in data.items()}

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=string_data,
                token=fcm_token
            )

            response = messaging.send(message)
            logger.info(f"Push notification sent successfully: {response}")
            return True

        except messaging.UnregisteredError:
            logger.warning(f"Invalid or expired FCM token: {fcm_token[:20]}...")
            return False
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    async def send_push_to_user(
        self,
        user_id: UUID,
        fcm_token: Optional[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send push notification to a user.

        Args:
            user_id: User ID (for logging)
            fcm_token: User's FCM token
            title: Notification title
            body: Notification body
            data: Additional data for deep linking

        Returns:
            True if sent successfully, False otherwise
        """
        if not fcm_token:
            logger.info(f"No FCM token for user {user_id} - skipping push")
            return False

        return await self.send_push(fcm_token, title, body, data)


# Global instance
push_service = PushService()
