import httpx
from typing import Dict, Any, Optional
from uuid import UUID
import logging
from app.core.config import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class NotificationClient:
    """
    Client for communicating with notification-service
    Sends booking events (request, approval, rejection)
    """
    
    def __init__(self):
        self.base_url = settings.NOTIFICATION_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
    
    async def _send_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Internal method to send event to notification service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/notifications/send/{event_type}",
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Notification sent for {event_type}")
                    return True
                else:
                    logger.error(f"Failed to send notification: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error calling notification service: {e}")
            return False

    async def send_booking_request(
        self,
        driver_id: UUID,
        booking_id: UUID,
        passenger_name: str,
        driver_name: str, # Ideally fetch or pass
        origin: str,
        destination: str,
        departure_time: str,
        seats_booked: int,
        total_amount: float,
        passenger_notes: Optional[str] = None
    ):
        """Send booking request notification to driver"""
        data = {
            "driver_id": str(driver_id),
            "booking_id": str(booking_id),
            "passenger_name": passenger_name,
            "driver_name": driver_name,
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "seats_booked": seats_booked,
            "total_amount": total_amount,
            "passenger_notes": passenger_notes,
            # Placeholder IDs mandated by schema but unused in this specific call
            "passenger_id": str(driver_id) # Should be ignored by service for this type
        }
        return await self._send_event("booking-request", data)

    async def send_booking_approved(
        self,
        passenger_id: UUID,
        booking_id: UUID,
        passenger_name: str,
        driver_name: str,
        origin: str,
        destination: str,
        departure_time: str,
        seats_booked: int,
        total_amount: float
    ):
        """Send booking approved notification to passenger"""
        data = {
            "passenger_id": str(passenger_id),
            "booking_id": str(booking_id),
            "passenger_name": passenger_name,
            "driver_name": driver_name,
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "seats_booked": seats_booked,
            "total_amount": total_amount,
            "driver_id": str(passenger_id) # Placeholder
        }
        return await self._send_event("booking-approved", data)

    async def send_booking_rejected(
        self,
        passenger_id: UUID,
        booking_id: UUID,
        passenger_name: str,
        origin: str,
        destination: str,
        departure_time: str,
        seats_booked: int
    ):
        """Send booking rejected notification to passenger"""
        data = {
            "passenger_id": str(passenger_id),
            "booking_id": str(booking_id),
            "passenger_name": passenger_name,
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "seats_booked": seats_booked,
            # Placeholders
            "driver_id": str(passenger_id),
            "driver_name": "System",
            "total_amount": 0.0
        }
        return await self._send_event("booking-rejected", data)

    async def send_payment_confirmation(
        self,
        passenger_id: UUID,
        booking_id: UUID,
        amount: float
    ):
        """Send payment confirmation notification"""
        data = {
            "passenger_id": str(passenger_id),
            "booking_id": str(booking_id),
            "amount": amount
        }
        return await self._send_event("payment-confirmation", data)

notification_client = NotificationClient()
