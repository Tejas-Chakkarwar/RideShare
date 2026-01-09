import httpx
from typing import Dict, Any
from uuid import UUID
import logging
# We need NOTIFICATION_SERVICE_URL in config, assuming generic base URL or hardcoded for now?
# Or use "http://notification-service:8000" if standard.
# Let's check config.py... I didn't add NOTIFICATION_SERVICE_URL there. I should defaults.
NOTIFICATION_SERVICE_URL = "http://notification-service:8000"

logger = logging.getLogger(__name__)

class NotificationClient:
    def __init__(self):
        self.base_url = NOTIFICATION_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
    
    async def _send_event(self, event_type: str, data: Dict[str, Any]):
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                await client.post(
                    f"{self.base_url}/api/v1/notifications/send/{event_type}",
                    json=data
                )
        except Exception as e:
            logger.error(f"Error sending notification event {event_type}: {e}")

    async def send_driver_approaching(self, passenger_id: UUID, data: Dict[str, Any]):
        # data needs: driver_name, eta_minutes
        # Notification service needs an endpoint for this.
        # "driver-approaching"
        payload = {
            "passenger_id": str(passenger_id),
            "driver_name": data.get("driver_name"),
            "eta_minutes": data.get("eta_minutes")
        }
        await self._send_event("driver-approaching", payload)

    async def send_driver_arrived(self, passenger_id: UUID, data: Dict[str, Any]):
        # "driver-arrived"
        payload = {
            "passenger_id": str(passenger_id),
            "driver_name": data.get("driver_name")
        }
        await self._send_event("driver-arrived", payload)

notification_client = NotificationClient()
