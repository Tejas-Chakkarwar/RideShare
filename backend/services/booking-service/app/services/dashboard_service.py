from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from uuid import UUID
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.models.booking import Booking, BookingStatus
from app.clients.ride_client import ride_client

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_driver_dashboard(self, driver_id: UUID) -> Dict[str, Any]:
        """
        Get dashboard stats for a driver.
        Aggregates data from their rides and bookings.
        """
        # 1. Get all rides for this driver from Ride Service
        rides = await ride_client.get_rides_by_driver(driver_id)
        if not rides:
            return {
                "total_earnings": 0.0,
                "completed_rides": 0,
                "upcoming_rides_count": 0,
                "recent_bookings": []
            }
            
        ride_ids = [UUID(ride['id']) for ride in rides]
        
        # 2. Query Bookings for these rides
        # Calculate Earnings (Completed bookings)
        earnings_query = select(func.sum(Booking.total_amount)).where(
            Booking.ride_id.in_(ride_ids),
            Booking.status == BookingStatus.COMPLETED
        )
        earnings_result = await self.db.execute(earnings_query)
        total_earnings = earnings_result.scalar() or 0.0
        
        # Count Completed Rides (Unique rides that have at least one completed booking is imprecise, 
        # but typically a ride is "completed" in ride service. 
        # Here we count completed bookings or completed rides? 
        # Dashboard usually shows "Rides provided". 
        # If we count bookings, it's passengers transported.
        # Let's count unique rides with completed status (from ride service data))
        
        completed_rides_count = sum(1 for r in rides if r.get('status') == 'completed')
        upcoming_rides_count = sum(1 for r in rides if r.get('status') == 'active')

        # Recent Activity (Bookings)
        # Get latest 5 bookings for these rides
        recent_query = select(Booking).where(
            Booking.ride_id.in_(ride_ids)
        ).order_by(Booking.created_at.desc()).limit(5)
        
        recent_result = await self.db.execute(recent_query)
        recent_bookings = recent_result.scalars().all()
        
        return {
            "total_earnings": float(total_earnings),
            "completed_rides": completed_rides_count,
            "upcoming_rides_count": upcoming_rides_count,
            "recent_bookings": [b.to_dict() for b in recent_bookings]
        }
