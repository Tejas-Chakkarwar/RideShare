from app.utils.geo import haversine_distance
from app.schemas.tracking import GeofenceEvent
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GeofenceService:
    """
    Detect when driver crosses geofence boundaries
    (approaching pickup, arrived at pickup, arrived at destination)
    """
    
    # Geofence thresholds
    APPROACHING_THRESHOLD_METERS = 500  # 500m = approaching
    ARRIVED_THRESHOLD_METERS = 100      # 100m = arrived
    
    def __init__(self):
        # Track last known state for each ride to prevent duplicate events
        self.last_states: dict = {}
    
    async def check_geofence(
        self,
        ride_id: UUID,
        current_lat: float,
        current_lng: float,
        pickup_lat: float,
        pickup_lng: float,
        destination_lat: float,
        destination_lng: float
    ) -> list[GeofenceEvent]:
        """
        Check if driver has crossed any geofence boundaries
        
        Returns:
            List of GeofenceEvent objects
        """
        events = []
        ride_key = str(ride_id)
        
        # Calculate distances
        distance_to_pickup = haversine_distance(
            current_lat, current_lng,
            pickup_lat, pickup_lng
        ) * 1000  # Convert to meters
        
        distance_to_destination = haversine_distance(
            current_lat, current_lng,
            destination_lat, destination_lng
        ) * 1000
        
        # Initialize state if not exists
        if ride_key not in self.last_states:
            self.last_states[ride_key] = {
                "approaching_pickup": False,
                "arrived_pickup": False,
                "approaching_destination": False,
                "arrived_destination": False
            }
        
        state = self.last_states[ride_key]
        
        # Check pickup geofences
        if not state["arrived_pickup"]:
            if distance_to_pickup <= self.ARRIVED_THRESHOLD_METERS:
                if not state["arrived_pickup"]:
                    events.append(GeofenceEvent(
                        event_type="arrived_pickup",
                        ride_id=ride_id,
                        location_type="pickup",
                        distance_meters=distance_to_pickup,
                        timestamp=datetime.utcnow()
                    ))
                    state["arrived_pickup"] = True
                    logger.info(f"Driver arrived at pickup for ride {ride_id}")
            
            elif distance_to_pickup <= self.APPROACHING_THRESHOLD_METERS:
                if not state["approaching_pickup"]:
                    events.append(GeofenceEvent(
                        event_type="approaching_pickup",
                        ride_id=ride_id,
                        location_type="pickup",
                        distance_meters=distance_to_pickup,
                        timestamp=datetime.utcnow()
                    ))
                    state["approaching_pickup"] = True
                    logger.info(f"Driver approaching pickup for ride {ride_id}")
        
        # Check destination geofences (only after pickup)
        if state["arrived_pickup"]:
            if distance_to_destination <= self.ARRIVED_THRESHOLD_METERS:
                if not state["arrived_destination"]:
                    events.append(GeofenceEvent(
                        event_type="arrived_destination",
                        ride_id=ride_id,
                        location_type="destination",
                        distance_meters=distance_to_destination,
                        timestamp=datetime.utcnow()
                    ))
                    state["arrived_destination"] = True
                    logger.info(f"Driver arrived at destination for ride {ride_id}")
            
            elif distance_to_destination <= self.APPROACHING_THRESHOLD_METERS:
                state_approaching = state.get("approaching_destination", False)
                if not state_approaching:
                    events.append(GeofenceEvent(
                        event_type="approaching_destination",
                        ride_id=ride_id,
                        location_type="destination",
                        distance_meters=distance_to_destination,
                        timestamp=datetime.utcnow()
                    ))
                    state["approaching_destination"] = True
        
        return events
    
    def reset_state(self, ride_id: UUID):
        """Reset geofence state for a ride (when ride completes)"""
        ride_key = str(ride_id)
        if ride_key in self.last_states:
            del self.last_states[ride_key]

geofence_service = GeofenceService()
