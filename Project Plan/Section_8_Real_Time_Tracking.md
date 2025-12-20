# SJSU RideShare Development Guide
## Section 8: Real-Time Tracking Service

**Version:** 1.0  
**Duration:** Week 8  
**Focus:** WebSocket-based real-time location tracking for active rides

---

# SECTION 8: Real-Time Tracking Service

## Learning Objectives
- Implement WebSocket connections with FastAPI
- Build real-time location broadcasting system
- Use Redis PubSub for scaling WebSocket connections
- Calculate ETA dynamically
- Implement geofencing for pickup/dropoff detection
- Handle connection management and reconnections
- Secure WebSocket connections with JWT

## Technologies
- FastAPI WebSocket
- Redis PubSub
- asyncio for concurrent operations
- Geospatial calculations
- JWT authentication for WebSocket
- Connection state management

## Prerequisites
- Sections 1-7 completed ✅
- Understanding of WebSocket protocol
- Understanding of publish-subscribe pattern
- Redis running and accessible
- Booking service operational

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Real-Time Tracking Service

CONTEXT:
Sections 1-7 completed. Bookings and notifications working.
Creating tracking-service for real-time location updates during active rides.
Section 8 of 13.

GOAL:
Build WebSocket-based tracking service that:
- Allows drivers to broadcast their location
- Allows passengers to receive live location updates
- Calculates real-time ETA
- Detects arrival at pickup/dropoff points (geofencing)
- Scales using Redis PubSub
- Handles connections/disconnections gracefully

DETAILED REQUIREMENTS:

1. CREATE TRACKING-SERVICE STRUCTURE:

   backend/services/tracking-service/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── api/
   │   │   └── routes/
   │   │       ├── health.py
   │   │       └── tracking.py
   │   ├── core/
   │   │   ├── config.py
   │   │   ├── redis_client.py
   │   │   └── exceptions.py
   │   ├── models/
   │   │   └── location.py
   │   ├── schemas/
   │   │   └── tracking.py
   │   ├── services/
   │   │   ├── tracking_service.py
   │   │   ├── geofence_service.py
   │   │   └── eta_service.py
   │   ├── websocket/
   │   │   ├── connection_manager.py
   │   │   └── pubsub_handler.py
   │   └── utils/
   │       └── auth.py
   ├── tests/
   ├── Dockerfile
   ├── requirements.txt
   └── README.md

2. LOCATION DATA MODEL:

   Since this is real-time data with short lifespan, store in Redis:
   
   Redis Key Structure:
   ```python
   # Current driver location
   Key: "location:ride:{ride_id}:driver"
   Value (JSON): {
       "user_id": "uuid",
       "lat": 37.3352,
       "lng": -121.8811,
       "speed": 25.5,  # km/h
       "bearing": 45.0,  # degrees (0-360)
       "accuracy": 10.0,  # meters
       "timestamp": "2024-12-17T10:30:00Z"
   }
   TTL: 86400 seconds (24 hours)
   
   # Location history (last 50 points for route replay)
   Key: "location:ride:{ride_id}:history"
   Value: List of location objects
   TTL: 86400 seconds
   
   # Active ride tracking status
   Key: "tracking:ride:{ride_id}:status"
   Value (JSON): {
       "is_active": true,
       "started_at": "timestamp",
       "driver_id": "uuid",
       "passenger_ids": ["uuid1", "uuid2"]
   }
   TTL: 86400 seconds
   ```

3. PYDANTIC SCHEMAS (app/schemas/tracking.py):

   ```python
   from pydantic import BaseModel, Field
   from typing import Optional, List
   from datetime import datetime
   from uuid import UUID
   
   class LocationUpdate(BaseModel):
       """Location update from driver"""
       lat: float = Field(..., ge=-90, le=90)
       lng: float = Field(..., ge=-180, le=180)
       speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
       bearing: Optional[float] = Field(None, ge=0, lt=360, description="Bearing in degrees")
       accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")
       timestamp: datetime
   
   class LocationResponse(BaseModel):
       """Location data sent to passengers"""
       driver_id: UUID
       lat: float
       lng: float
       speed: Optional[float]
       bearing: Optional[float]
       timestamp: datetime
       eta_seconds: Optional[int] = None
       distance_remaining_km: Optional[float] = None
   
   class TrackingStatus(BaseModel):
       """Current tracking status"""
       ride_id: UUID
       is_active: bool
       driver_connected: bool
       passengers_connected: int
       current_location: Optional[LocationResponse]
       
   class GeofenceEvent(BaseModel):
       """Geofence crossing event"""
       event_type: str  # "approaching_pickup", "arrived_pickup", "arrived_destination"
       ride_id: UUID
       location_type: str  # "pickup", "destination"
       distance_meters: float
       timestamp: datetime
   ```

4. REDIS CLIENT SETUP (app/core/redis_client.py):

   ```python
   import redis.asyncio as redis
   from app.core.config import settings
   import json
   import logging
   
   logger = logging.getLogger(__name__)
   
   class RedisClient:
       """Async Redis client for tracking service"""
       
       def __init__(self):
           self.redis = None
           self.pubsub = None
       
       async def connect(self):
           """Establish Redis connection"""
           self.redis = await redis.from_url(
               settings.REDIS_URL,
               encoding="utf-8",
               decode_responses=True
           )
           self.pubsub = self.redis.pubsub()
           logger.info("Redis connected")
       
       async def disconnect(self):
           """Close Redis connection"""
           if self.pubsub:
               await self.pubsub.close()
           if self.redis:
               await self.redis.close()
           logger.info("Redis disconnected")
       
       async def publish_location(self, ride_id: str, location_data: dict):
           """Publish location update to Redis PubSub channel"""
           channel = f"ride:{ride_id}:location"
           message = json.dumps(location_data)
           await self.redis.publish(channel, message)
           logger.debug(f"Published location to {channel}")
       
       async def subscribe_location(self, ride_id: str):
           """Subscribe to location updates for a ride"""
           channel = f"ride:{ride_id}:location"
           await self.pubsub.subscribe(channel)
           logger.info(f"Subscribed to {channel}")
       
       async def unsubscribe_location(self, ride_id: str):
           """Unsubscribe from location updates"""
           channel = f"ride:{ride_id}:location"
           await self.pubsub.unsubscribe(channel)
           logger.info(f"Unsubscribed from {channel}")
       
       async def store_location(self, ride_id: str, location_data: dict):
           """Store current location in Redis"""
           key = f"location:ride:{ride_id}:driver"
           await self.redis.setex(
               key,
               86400,  # 24 hour expiry
               json.dumps(location_data)
           )
       
       async def get_location(self, ride_id: str) -> dict:
           """Get current driver location"""
           key = f"location:ride:{ride_id}:driver"
           data = await self.redis.get(key)
           return json.loads(data) if data else None
       
       async def add_to_history(self, ride_id: str, location_data: dict):
           """Add location to history (keep last 50 points)"""
           key = f"location:ride:{ride_id}:history"
           await self.redis.lpush(key, json.dumps(location_data))
           await self.redis.ltrim(key, 0, 49)  # Keep only last 50
           await self.redis.expire(key, 86400)
       
       async def get_history(self, ride_id: str) -> List[dict]:
           """Get location history"""
           key = f"location:ride:{ride_id}:history"
           data = await self.redis.lrange(key, 0, -1)
           return [json.loads(item) for item in data]
   
   # Global instance
   redis_client = RedisClient()
   ```

5. CONNECTION MANAGER (app/websocket/connection_manager.py):

   ```python
   from fastapi import WebSocket
   from typing import Dict, Set
   from uuid import UUID
   import logging
   import asyncio
   
   logger = logging.getLogger(__name__)
   
   class ConnectionManager:
       """
       Manages WebSocket connections for drivers and passengers
       Handles broadcasting, disconnections, and connection state
       """
       
       def __init__(self):
           # ride_id -> set of passenger websockets
           self.passenger_connections: Dict[str, Set[WebSocket]] = {}
           
           # ride_id -> driver websocket
           self.driver_connections: Dict[str, WebSocket] = {}
           
           # websocket -> user info
           self.connection_info: Dict[WebSocket, dict] = {}
       
       async def connect_driver(
           self,
           websocket: WebSocket,
           ride_id: str,
           driver_id: str
       ):
           """Connect driver for a ride"""
           await websocket.accept()
           
           # Disconnect existing driver if any
           if ride_id in self.driver_connections:
               old_ws = self.driver_connections[ride_id]
               await self.disconnect_driver(old_ws, ride_id)
           
           self.driver_connections[ride_id] = websocket
           self.connection_info[websocket] = {
               "type": "driver",
               "ride_id": ride_id,
               "user_id": driver_id
           }
           
           logger.info(f"Driver {driver_id} connected to ride {ride_id}")
       
       async def connect_passenger(
           self,
           websocket: WebSocket,
           ride_id: str,
           passenger_id: str
       ):
           """Connect passenger to track a ride"""
           await websocket.accept()
           
           if ride_id not in self.passenger_connections:
               self.passenger_connections[ride_id] = set()
           
           self.passenger_connections[ride_id].add(websocket)
           self.connection_info[websocket] = {
               "type": "passenger",
               "ride_id": ride_id,
               "user_id": passenger_id
           }
           
           logger.info(f"Passenger {passenger_id} connected to ride {ride_id}")
       
       async def disconnect_driver(self, websocket: WebSocket, ride_id: str):
           """Disconnect driver"""
           if ride_id in self.driver_connections:
               if self.driver_connections[ride_id] == websocket:
                   del self.driver_connections[ride_id]
           
           if websocket in self.connection_info:
               del self.connection_info[websocket]
           
           logger.info(f"Driver disconnected from ride {ride_id}")
       
       async def disconnect_passenger(self, websocket: WebSocket, ride_id: str):
           """Disconnect passenger"""
           if ride_id in self.passenger_connections:
               self.passenger_connections[ride_id].discard(websocket)
               
               # Clean up empty sets
               if not self.passenger_connections[ride_id]:
                   del self.passenger_connections[ride_id]
           
           if websocket in self.connection_info:
               del self.connection_info[websocket]
           
           logger.info(f"Passenger disconnected from ride {ride_id}")
       
       async def broadcast_to_passengers(
           self,
           ride_id: str,
           message: dict
       ):
           """Broadcast location update to all passengers of a ride"""
           if ride_id not in self.passenger_connections:
               return
           
           dead_connections = set()
           
           for websocket in self.passenger_connections[ride_id]:
               try:
                   await websocket.send_json(message)
               except Exception as e:
                   logger.error(f"Error broadcasting to passenger: {e}")
                   dead_connections.add(websocket)
           
           # Remove dead connections
           for ws in dead_connections:
               await self.disconnect_passenger(ws, ride_id)
       
       def get_passenger_count(self, ride_id: str) -> int:
           """Get number of connected passengers for a ride"""
           return len(self.passenger_connections.get(ride_id, set()))
       
       def is_driver_connected(self, ride_id: str) -> bool:
           """Check if driver is connected"""
           return ride_id in self.driver_connections
       
       async def send_to_driver(self, ride_id: str, message: dict):
           """Send message to driver"""
           if ride_id in self.driver_connections:
               try:
                   await self.driver_connections[ride_id].send_json(message)
               except Exception as e:
                   logger.error(f"Error sending to driver: {e}")
       
       def get_active_rides(self) -> list:
           """Get list of rides with active tracking"""
           return list(set(
               list(self.driver_connections.keys()) +
               list(self.passenger_connections.keys())
           ))
   
   # Global connection manager
   manager = ConnectionManager()
   ```

6. ETA SERVICE (app/services/eta_service.py):

   ```python
   from app.utils.geo import haversine_distance
   from typing import Optional
   import logging
   
   logger = logging.getLogger(__name__)
   
   class ETAService:
       """Calculate estimated time of arrival"""
       
       @staticmethod
       def calculate_eta(
           current_lat: float,
           current_lng: float,
           destination_lat: float,
           destination_lng: float,
           current_speed_kmh: Optional[float] = None,
           average_speed_kmh: float = 40.0  # Default average speed
       ) -> dict:
           """
           Calculate ETA to destination
           
           Returns:
               dict with eta_seconds, distance_km, estimated_arrival_time
           """
           # Calculate distance
           distance_km = haversine_distance(
               current_lat, current_lng,
               destination_lat, destination_lng
           )
           
           # Determine speed to use
           speed = current_speed_kmh if current_speed_kmh and current_speed_kmh > 0 else average_speed_kmh
           
           # Calculate time in hours, then convert to seconds
           time_hours = distance_km / speed
           eta_seconds = int(time_hours * 3600)
           
           # Add buffer for stops, traffic (20%)
           eta_seconds = int(eta_seconds * 1.2)
           
           from datetime import datetime, timedelta
           estimated_arrival = datetime.utcnow() + timedelta(seconds=eta_seconds)
           
           return {
               "eta_seconds": eta_seconds,
               "distance_km": round(distance_km, 2),
               "estimated_arrival_time": estimated_arrival.isoformat()
           }
   
   eta_service = ETAService()
   ```

7. GEOFENCE SERVICE (app/services/geofence_service.py):

   ```python
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
                   if not state["approaching_destination"]:
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
   ```

8. WEBSOCKET AUTHENTICATION (app/utils/auth.py):

   ```python
   from fastapi import WebSocket, status, Query
   from jose import jwt, JWTError
   from app.core.config import settings
   from uuid import UUID
   import logging
   
   logger = logging.getLogger(__name__)
   
   async def authenticate_websocket(
       websocket: WebSocket,
       token: str = Query(...)
   ) -> dict:
       """
       Authenticate WebSocket connection using JWT token
       
       Returns:
           dict with user_id and email if valid
       
       Raises:
           Closes WebSocket with 403 if invalid
       """
       try:
           # Decode JWT token
           payload = jwt.decode(
               token,
               settings.SECRET_KEY,
               algorithms=[settings.ALGORITHM]
           )
           
           user_id = payload.get("user_id")
           email = payload.get("email")
           
           if not user_id or not email:
               await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
               raise Exception("Invalid token payload")
           
           return {
               "user_id": user_id,
               "email": email
           }
       
       except JWTError as e:
           logger.error(f"JWT validation failed: {e}")
           await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
           raise Exception("Invalid or expired token")
   ```

9. TRACKING API ROUTES (app/api/routes/tracking.py):

   ```python
   from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
   from uuid import UUID
   from typing import Optional
   import asyncio
   import logging
   
   from app.websocket.connection_manager import manager
   from app.core.redis_client import redis_client
   from app.schemas.tracking import LocationUpdate, LocationResponse
   from app.services.eta_service import eta_service
   from app.services.geofence_service import geofence_service
   from app.utils.auth import authenticate_websocket
   from app.clients.booking_client import booking_client
   from app.clients.notification_client import notification_client
   
   router = APIRouter()
   logger = logging.getLogger(__name__)
   
   @router.websocket("/ride/{ride_id}/driver")
   async def driver_tracking(
       websocket: WebSocket,
       ride_id: UUID,
       token: str = Query(...)
   ):
       """
       WebSocket endpoint for drivers to send location updates
       
       Flow:
       1. Authenticate driver
       2. Verify driver owns the ride
       3. Accept connection
       4. Receive location updates
       5. Broadcast to passengers
       6. Check geofences
       7. Calculate ETA
       """
       try:
           # Authenticate
           user_data = await authenticate_websocket(websocket, token)
           driver_id = user_data["user_id"]
           
           # Verify driver owns this ride
           ride = await ride_client.get_ride(ride_id)
           if not ride or ride["driver_id"] != driver_id:
               await websocket.close(code=1008)
               return
           
           # Get booking details for geofencing
           bookings = await booking_client.get_ride_bookings(ride_id)
           if not bookings:
               logger.warning(f"No bookings for ride {ride_id}")
           
           # Connect driver
           await manager.connect_driver(websocket, str(ride_id), driver_id)
           
           # Send initial confirmation
           await websocket.send_json({
               "type": "connected",
               "message": "Tracking started",
               "ride_id": str(ride_id),
               "passengers_connected": manager.get_passenger_count(str(ride_id))
           })
           
           while True:
               # Receive location update from driver
               data = await websocket.receive_json()
               
               # Validate and parse
               location_update = LocationUpdate(**data)
               
               # Store in Redis
               location_data = {
                   "driver_id": driver_id,
                   "lat": location_update.lat,
                   "lng": location_update.lng,
                   "speed": location_update.speed,
                   "bearing": location_update.bearing,
                   "accuracy": location_update.accuracy,
                   "timestamp": location_update.timestamp.isoformat()
               }
               
               await redis_client.store_location(str(ride_id), location_data)
               await redis_client.add_to_history(str(ride_id), location_data)
               
               # Calculate ETA to destination
               eta_data = eta_service.calculate_eta(
                   location_update.lat,
                   location_update.lng,
                   ride["destination_lat"],
                   ride["destination_lng"],
                   location_update.speed
               )
               
               # Check geofences for each booking
               for booking in bookings:
                   geofence_events = await geofence_service.check_geofence(
                       ride_id,
                       location_update.lat,
                       location_update.lng,
                       booking["pickup_location"]["lat"],
                       booking["pickup_location"]["lng"],
                       booking["dropoff_location"]["lat"],
                       booking["dropoff_location"]["lng"]
                   )
                   
                   # Send notifications for geofence events
                   for event in geofence_events:
                       if event.event_type == "approaching_pickup":
                           await notification_client.send_driver_approaching(
                               booking["passenger_id"],
                               {
                                   "driver_name": ride["driver_name"],
                                   "eta_minutes": eta_data["eta_seconds"] // 60
                               }
                           )
                       elif event.event_type == "arrived_pickup":
                           await notification_client.send_driver_arrived(
                               booking["passenger_id"],
                               {"driver_name": ride["driver_name"]}
                           )
               
               # Prepare broadcast message
               broadcast_message = {
                   "type": "location_update",
                   "driver_id": driver_id,
                   "lat": location_update.lat,
                   "lng": location_update.lng,
                   "speed": location_update.speed,
                   "bearing": location_update.bearing,
                   "timestamp": location_update.timestamp.isoformat(),
                   "eta_seconds": eta_data["eta_seconds"],
                   "distance_remaining_km": eta_data["distance_km"]
               }
               
               # Broadcast to passengers via Redis PubSub
               await redis_client.publish_location(str(ride_id), broadcast_message)
               
               # Also broadcast directly to connected passengers
               await manager.broadcast_to_passengers(str(ride_id), broadcast_message)
       
       except WebSocketDisconnect:
           logger.info(f"Driver disconnected from ride {ride_id}")
       except Exception as e:
           logger.error(f"Error in driver tracking: {e}")
       finally:
           await manager.disconnect_driver(websocket, str(ride_id))
   
   @router.websocket("/ride/{ride_id}/passenger")
   async def passenger_tracking(
       websocket: WebSocket,
       ride_id: UUID,
       token: str = Query(...)
   ):
       """
       WebSocket endpoint for passengers to receive driver location updates
       
       Flow:
       1. Authenticate passenger
       2. Verify passenger has booking for this ride
       3. Accept connection
       4. Subscribe to Redis PubSub for location updates
       5. Forward updates to passenger
       """
       try:
           # Authenticate
           user_data = await authenticate_websocket(websocket, token)
           passenger_id = user_data["user_id"]
           
           # Verify passenger has booking
           booking = await booking_client.get_passenger_booking(passenger_id, ride_id)
           if not booking or booking["status"] not in ["approved", "completed"]:
               await websocket.close(code=1008)
               return
           
           # Connect passenger
           await manager.connect_passenger(websocket, str(ride_id), passenger_id)
           
           # Send initial confirmation with last known location
           last_location = await redis_client.get_location(str(ride_id))
           await websocket.send_json({
               "type": "connected",
               "message": "Tracking connected",
               "ride_id": str(ride_id),
               "current_location": last_location
           })
           
           # Subscribe to Redis PubSub for this ride
           await redis_client.subscribe_location(str(ride_id))
           
           # Listen for updates
           async for message in redis_client.pubsub.listen():
               if message["type"] == "message":
                   # Forward to passenger
                   location_data = json.loads(message["data"])
                   await websocket.send_json(location_data)
       
       except WebSocketDisconnect:
           logger.info(f"Passenger disconnected from ride {ride_id}")
       except Exception as e:
           logger.error(f"Error in passenger tracking: {e}")
       finally:
           await redis_client.unsubscribe_location(str(ride_id))
           await manager.disconnect_passenger(websocket, str(ride_id))
   
   @router.get("/ride/{ride_id}/status")
   async def get_tracking_status(ride_id: UUID):
       """Get current tracking status for a ride (REST endpoint)"""
       return {
           "ride_id": str(ride_id),
           "driver_connected": manager.is_driver_connected(str(ride_id)),
           "passengers_connected": manager.get_passenger_count(str(ride_id)),
           "current_location": await redis_client.get_location(str(ride_id))
       }
   
   @router.get("/ride/{ride_id}/history")
   async def get_location_history(ride_id: UUID):
       """Get location history for a ride (for replay)"""
       history = await redis_client.get_history(str(ride_id))
       return {
           "ride_id": str(ride_id),
           "locations": history,
           "count": len(history)
       }
   ```

10. DOCKER CONFIGURATION:

    Update docker-compose.yml:
    ```yaml
    tracking-service:
      build: ./services/tracking-service
      ports: ["8005:8000"]
      environment:
        - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare
        - REDIS_URL=redis://redis:6379/0
        - RIDE_SERVICE_URL=http://ride-service:8000
        - BOOKING_SERVICE_URL=http://booking-service:8000
        - NOTIFICATION_SERVICE_URL=http://notification-service:8000
        - SECRET_KEY=${SECRET_KEY}
      depends_on: [redis, booking-service, notification-service]
    ```

11. MAIN APPLICATION (app/main.py):

    ```python
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import logging
    
    from app.api.routes import tracking, health
    from app.core.redis_client import redis_client
    from app.core.config import settings
    
    # Setup logging
    logging.basicConfig(level=settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    app = FastAPI(
        title="SJSU RideShare Tracking Service",
        description="Real-time location tracking for active rides",
        version="1.0.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])
    
    @app.on_event("startup")
    async def startup():
        """Connect to Redis on startup"""
        await redis_client.connect()
        logger.info("Tracking service started")
    
    @app.on_event("shutdown")
    async def shutdown():
        """Disconnect from Redis on shutdown"""
        await redis_client.disconnect()
        logger.info("Tracking service stopped")
    ```

12. REQUIREMENTS.txt:

    ```
    fastapi==0.104.1
    uvicorn[standard]==0.24.0
    websockets==12.0
    redis==5.0.1
    python-jose[cryptography]==3.3.0
    pydantic==2.5.0
    pydantic-settings==2.1.0
    python-dotenv==1.0.0
    httpx==0.25.2
    ```

13. GENERATE LEARNING DOCUMENTATION:

    Create: docs/learning/08-real-time-tracking.md
    
    Cover (20+ pages):
    1. WebSocket Protocol
       - How WebSocket works
       - Difference from HTTP
       - Connection lifecycle
       - Message framing
    
    2. Real-Time Architecture
       - Push vs Pull
       - Scaling WebSocket connections
       - Connection management
    
    3. Redis PubSub
       - Publisher-Subscriber pattern
       - Channels and subscriptions
       - Scaling with PubSub
       - Use cases
    
    4. Location Tracking
       - GPS accuracy
       - Location updates frequency
       - Battery optimization
       - Privacy considerations
    
    5. ETA Calculation
       - Distance vs time
       - Speed considerations
       - Traffic estimation
       - Route optimization
    
    6. Geofencing
       - What is geofencing
       - Detection algorithms
       - Threshold selection
       - Event triggering
    
    7. Connection Management
       - Handling disconnects
       - Reconnection logic
       - State synchronization
       - Heartbeat/ping-pong
    
    8. Security
       - WebSocket authentication
       - Token validation
       - Connection authorization
    
    9. Testing WebSockets
       - Unit testing
       - Integration testing
       - Load testing
       - Tools

14. TESTING (tests/test_tracking.py):

    ```python
    import pytest
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    def test_websocket_driver_connection():
        """Test driver can connect via WebSocket"""
        with client.websocket_connect(
            "/api/v1/tracking/ride/test-ride-id/driver?token=valid_jwt_token"
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
    
    def test_websocket_passenger_receives_updates():
        """Test passenger receives location updates"""
        # Connect driver
        # Send location update
        # Connect passenger
        # Verify passenger receives update
        pass
    
    def test_eta_calculation():
        """Test ETA calculation"""
        from app.services.eta_service import eta_service
        
        result = eta_service.calculate_eta(
            37.3352, -121.8811,  # SJSU
            37.6213, -122.3790,  # SFO
            current_speed_kmh=60
        )
        
        assert result["eta_seconds"] > 0
        assert result["distance_km"] > 0
    
    def test_geofence_detection():
        """Test geofence event detection"""
        # Test approaching
        # Test arrived
        # Test no duplicate events
        pass
    ```

15. CLIENT-SIDE USAGE EXAMPLE:

    For React Native mobile app:
    ```javascript
    // Driver sending location
    const ws = new WebSocket(
      `ws://api.sjsurideshare.com/api/v1/tracking/ride/${rideId}/driver?token=${token}`
    );
    
    ws.onopen = () => {
      // Start sending location every 5 seconds
      setInterval(() => {
        navigator.geolocation.getCurrentPosition(position => {
          ws.send(JSON.stringify({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            speed: position.coords.speed * 3.6, // m/s to km/h
            bearing: position.coords.heading,
            accuracy: position.coords.accuracy,
            timestamp: new Date().toISOString()
          }));
        });
      }, 5000);
    };
    
    // Passenger receiving location
    const ws = new WebSocket(
      `ws://api.sjsurideshare.com/api/v1/tracking/ride/${rideId}/passenger?token=${token}`
    );
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'location_update') {
        // Update map with driver location
        updateDriverMarker(data.lat, data.lng);
        // Update ETA display
        updateETA(data.eta_seconds);
      }
    };
    ```

CRITICAL REQUIREMENTS:

WebSocket Management:
- Proper connection lifecycle
- Graceful disconnection handling
- Reconnection logic on client
- Authentication before acceptance

Performance:
- Location updates: 5-10 seconds interval
- Redis PubSub for scaling
- Efficient broadcasting
- Connection pooling

Real-Time:
- Sub-second latency
- Reliable message delivery
- Order preservation
- State synchronization

Security:
- JWT authentication
- Connection authorization
- Rate limiting
- Input validation

VERIFICATION CHECKLIST:
- [ ] Service runs on port 8005
- [ ] Driver can connect via WebSocket
- [ ] Driver can send location updates
- [ ] Passengers receive updates in real-time
- [ ] ETA calculated correctly
- [ ] Geofence detects approaching (500m)
- [ ] Geofence detects arrival (100m)
- [ ] Notifications sent on geofence events
- [ ] Multiple passengers can connect
- [ ] Handles disconnects gracefully
- [ ] Reconnection works
- [ ] Location stored in Redis
- [ ] History retrievable
- [ ] Redis PubSub working
- [ ] JWT authentication working
- [ ] Latency < 1 second
- [ ] All tests pass

Please generate tracking service with comprehensive WebSocket implementation.
```

---

## TESTING CHECKLIST - SECTION 8

### Setup
- [ ] Tracking-service created
- [ ] Port 8005 configured
- [ ] Redis accessible
- [ ] Dependencies installed

### WebSocket Connection - Driver
```javascript
// Test with WebSocket client
ws = new WebSocket('ws://localhost:8005/api/v1/tracking/ride/{ride_id}/driver?token={jwt}')
```
- [ ] Connection accepted
- [ ] Receives confirmation message
- [ ] Can send location updates
- [ ] Updates stored in Redis

### WebSocket Connection - Passenger
```javascript
ws = new WebSocket('ws://localhost:8005/api/v1/tracking/ride/{ride_id}/passenger?token={jwt}')
```
- [ ] Connection accepted
- [ ] Receives current location
- [ ] Receives real-time updates
- [ ] Updates match driver's location

### Location Updates
Send from driver:
```json
{
  "lat": 37.3352,
  "lng": -121.8811,
  "speed": 45.5,
  "bearing": 90.0,
  "accuracy": 10.0,
  "timestamp": "2024-12-17T10:30:00Z"
}
```
- [ ] Accepted and validated
- [ ] Stored in Redis
- [ ] Broadcasted to passengers
- [ ] Added to history

### ETA Calculation
Driver location: SJSU (37.3352, -121.8811)
Destination: SFO (37.6213, -122.3790)
Speed: 60 km/h
- [ ] ETA calculated
- [ ] Distance calculated (~55 km)
- [ ] ETA reasonable (~65 minutes with buffer)
- [ ] Updates dynamically

### Geofencing
Setup: Driver approaching pickup location

Test 1: 600m away
- [ ] No event triggered

Test 2: 400m away
- [ ] "approaching_pickup" event triggered
- [ ] Notification sent to passenger
- [ ] No duplicate events

Test 3: 50m away
- [ ] "arrived_pickup" event triggered
- [ ] Notification sent
- [ ] No duplicate events

Test 4: At destination
- [ ] "arrived_destination" event triggered

### Redis Storage
- [ ] Current location stored with key format
- [ ] 24 hour TTL set
- [ ] History maintained (last 50 points)
- [ ] History retrievable via API

### Redis PubSub
- [ ] Location published to channel
- [ ] Passengers subscribed to channel
- [ ] Messages received
- [ ] Works across multiple server instances

### Connection Management
- [ ] Multiple passengers can connect
- [ ] Passenger count accurate
- [ ] Disconnect handled gracefully
- [ ] Dead connections cleaned up
- [ ] Driver reconnect works

### Authentication
- [ ] Valid JWT accepted
- [ ] Invalid JWT rejected (403)
- [ ] Expired JWT rejected
- [ ] Connection closed on auth failure

### REST Endpoints
GET /api/v1/tracking/ride/{ride_id}/status
- [ ] Returns tracking status
- [ ] Shows driver connected status
- [ ] Shows passenger count
- [ ] Shows current location

GET /api/v1/tracking/ride/{ride_id}/history
- [ ] Returns location history
- [ ] Up to 50 points
- [ ] Ordered correctly

### Performance
- [ ] Location update latency < 500ms
- [ ] Broadcast latency < 1 second
- [ ] Handles 10 passengers per ride
- [ ] Handles 10 concurrent rides
- [ ] Memory usage reasonable
- [ ] CPU usage acceptable

### Error Handling
- [ ] Invalid location data rejected
- [ ] Network disconnects handled
- [ ] Redis connection failures handled
- [ ] Service restart reconnects

### Integration
- [ ] Works with booking service
- [ ] Calls notification service
- [ ] Geofence notifications sent
- [ ] Ride data retrieved

### Mobile App Integration
In React Native:
- [ ] Can connect from app
- [ ] Location permissions working
- [ ] Background location working
- [ ] Battery optimization applied
- [ ] Map updates in real-time

### Learning
- [ ] Read 08-real-time-tracking.md
- [ ] Understand WebSocket protocol
- [ ] Understand Redis PubSub
- [ ] Understand geofencing
- [ ] Can explain ETA calculation

### Completion
- [ ] All tests passing
- [ ] WebSocket connections stable
- [ ] Real-time tracking working
- [ ] Geofencing accurate
- [ ] Ready for Section 9

---

**Date Completed:** _______________  
**Concurrent Rides Tested:** _____  
**Passengers per Ride:** _____  
**Average Latency:** _______ ms  
**Notes:** _______________
