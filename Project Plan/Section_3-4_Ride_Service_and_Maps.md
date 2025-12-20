# SJSU RideShare Development Guide
## Sections 3-4: Ride Service & Google Maps Integration

**Version:** 1.0  
**Duration:** Week 3-4  
**Focus:** Ride CRUD Operations, Search, Geospatial Queries, Google Maps API

---

# TABLE OF CONTENTS

1. [Section 3: Ride Service Microservice](#section-3)
2. [Section 4: Google Maps Integration](#section-4)
3. [Testing Checklists](#testing)
4. [Common Issues & Solutions](#troubleshooting)

---

<a name="section-3"></a>
# SECTION 3: Ride Service - Post & Search Rides

## Learning Objectives
- Create new microservice from scratch
- Implement CRUD operations (Create, Read, Update, Delete)
- Database relationships across services
- Advanced SQLAlchemy queries with filtering
- Geospatial concepts and distance calculations
- Inter-service HTTP communication
- Search and filtering patterns

## Technologies
- FastAPI (new service)
- SQLAlchemy relationships
- Geospatial queries (lat/lng)
- Date/time handling (UTC)
- HTTPX (async HTTP client)
- Haversine distance formula

## Prerequisites
- Sections 1-2 completed and tested ✅
- User service running on port 8001
- Understanding of REST API design
- Basic understanding of latitude/longitude
- Familiarity with date/time concepts

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Ride Service Microservice

CONTEXT:
Sections 1-2 completed and tested. User authentication working with JWT tokens.
Now creating ride-service microservice for posting rides, searching rides, and managing ride listings.
This is Section 3 of 13.

SECTION 3 GOAL:
Build ride-service with ability to post rides, search rides with filters, manage ride listings,
and calculate distances. Drivers can post rides with pickup/destination, and passengers can search
for relevant rides.

DETAILED REQUIREMENTS:

1. CREATE RIDE-SERVICE STRUCTURE:
   
   Create new service with structure similar to user-service:
   
   backend/services/ride-service/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── api/
   │   │   └── routes/
   │   │       ├── __init__.py
   │   │       ├── health.py
   │   │       └── rides.py
   │   ├── core/
   │   │   ├── __init__.py
   │   │   ├── config.py
   │   │   ├── database.py
   │   │   └── exceptions.py
   │   ├── models/
   │   │   ├── __init__.py
   │   │   └── ride.py
   │   ├── schemas/
   │   │   ├── __init__.py
   │   │   └── ride.py
   │   ├── services/
   │   │   ├── __init__.py
   │   │   └── ride_service.py
   │   ├── clients/
   │   │   ├── __init__.py
   │   │   └── user_client.py
   │   └── utils/
   │       ├── __init__.py
   │       └── geo.py
   ├── alembic/
   │   ├── versions/
   │   └── env.py
   ├── tests/
   │   ├── __init__.py
   │   └── test_rides.py
   ├── .env.example
   ├── .gitignore
   ├── Dockerfile
   ├── requirements.txt
   ├── alembic.ini
   └── README.md

2. RIDE MODEL (app/models/ride.py):
   
   Create comprehensive Ride model:
   
   ```python
   from sqlalchemy import (
       Column, String, Float, Integer, DateTime, Text, Boolean, Enum, JSON,
       Index, ForeignKey, Numeric
   )
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.sql import func
   import uuid
   import enum
   from app.core.database import Base
   
   class RideStatus(str, enum.Enum):
       """Enum for ride status"""
       ACTIVE = "active"
       FULL = "full"
       COMPLETED = "completed"
       CANCELLED = "cancelled"
   
   class Ride(Base):
       """
       Ride model for carpooling rides
       
       Attributes:
           id: Unique ride identifier
           driver_id: User ID of driver (foreign key to users.id)
           origin_address: Starting point address
           origin_lat: Starting point latitude
           origin_lng: Starting point longitude
           destination_address: End point address
           destination_lat: End point latitude
           destination_lng: End point longitude
           departure_time: When ride departs
           available_seats: Number of seats available (1-7)
           price_per_seat: Price per seat in USD (0 for free)
           vehicle_make: Vehicle manufacturer (e.g., Toyota)
           vehicle_model: Vehicle model (e.g., Camry)
           vehicle_year: Vehicle year
           vehicle_license_plate: License plate number
           vehicle_color: Vehicle color
           preferences: JSON with ride preferences
           status: Current ride status
           is_recurring: Whether ride repeats
           recurring_schedule: JSON with recurring details
           notes: Additional information
           created_at: When ride was posted
           updated_at: Last update time
       """
       __tablename__ = "rides"
       
       # Primary Key
       id = Column(
           UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4,
           unique=True,
           nullable=False
       )
       
       # Driver (foreign key to users table)
       driver_id = Column(
           UUID(as_uuid=True),
           nullable=False,
           index=True,
           comment="Reference to user who is driving"
       )
       
       # Origin location
       origin_address = Column(
           String(500),
           nullable=False,
           comment="Starting point address"
       )
       origin_lat = Column(
           Float,
           nullable=False,
           comment="Starting point latitude (-90 to 90)"
       )
       origin_lng = Column(
           Float,
           nullable=False,
           comment="Starting point longitude (-180 to 180)"
       )
       
       # Destination location
       destination_address = Column(
           String(500),
           nullable=False,
           comment="End point address"
       )
       destination_lat = Column(
           Float,
           nullable=False,
           comment="End point latitude (-90 to 90)"
       )
       destination_lng = Column(
           Float,
           nullable=False,
           comment="End point longitude (-180 to 180)"
       )
       
       # Ride details
       departure_time = Column(
           DateTime(timezone=True),
           nullable=False,
           index=True,
           comment="When ride departs (must be in future)"
       )
       available_seats = Column(
           Integer,
           nullable=False,
           comment="Available seats (1-7)"
       )
       price_per_seat = Column(
           Numeric(10, 2),
           nullable=False,
           default=0.00,
           comment="Price per seat in USD (0 for free)"
       )
       
       # Vehicle information
       vehicle_make = Column(
           String(100),
           nullable=False,
           comment="Vehicle manufacturer"
       )
       vehicle_model = Column(
           String(100),
           nullable=False,
           comment="Vehicle model"
       )
       vehicle_year = Column(
           Integer,
           nullable=False,
           comment="Vehicle year"
       )
       vehicle_license_plate = Column(
           String(20),
           nullable=False,
           comment="License plate number"
       )
       vehicle_color = Column(
           String(50),
           nullable=True,
           comment="Vehicle color"
       )
       
       # Preferences and options
       preferences = Column(
           JSON,
           nullable=True,
           default=dict,
           comment="Ride preferences (music, AC, stops, etc.)"
       )
       
       # Status
       status = Column(
           Enum(RideStatus),
           nullable=False,
           default=RideStatus.ACTIVE,
           index=True,
           comment="Current ride status"
       )
       
       # Recurring rides
       is_recurring = Column(
           Boolean,
           default=False,
           nullable=False,
           comment="Whether ride repeats on schedule"
       )
       recurring_schedule = Column(
           JSON,
           nullable=True,
           comment="Recurring schedule details"
       )
       
       # Additional information
       notes = Column(
           Text,
           nullable=True,
           comment="Additional ride information (max 1000 chars)"
       )
       
       # Timestamps
       created_at = Column(
           DateTime(timezone=True),
           server_default=func.now(),
           nullable=False,
           index=True
       )
       updated_at = Column(
           DateTime(timezone=True),
           server_default=func.now(),
           onupdate=func.now(),
           nullable=False
       )
       
       # Indexes for performance
       __table_args__ = (
           Index('ix_rides_driver_id', 'driver_id'),
           Index('ix_rides_departure_time', 'departure_time'),
           Index('ix_rides_status', 'status'),
           Index('ix_rides_origin_coords', 'origin_lat', 'origin_lng'),
           Index('ix_rides_destination_coords', 'destination_lat', 'destination_lng'),
           Index('ix_rides_created_at', 'created_at'),
       )
       
       def __repr__(self) -> str:
           return f"<Ride {self.id} from {self.origin_address} to {self.destination_address}>"
       
       def to_dict(self) -> dict:
           """Convert ride to dictionary"""
           return {
               "id": str(self.id),
               "driver_id": str(self.driver_id),
               "origin": {
                   "address": self.origin_address,
                   "lat": self.origin_lat,
                   "lng": self.origin_lng
               },
               "destination": {
                   "address": self.destination_address,
                   "lat": self.destination_lat,
                   "lng": self.destination_lng
               },
               "departure_time": self.departure_time.isoformat(),
               "available_seats": self.available_seats,
               "price_per_seat": float(self.price_per_seat),
               "vehicle": {
                   "make": self.vehicle_make,
                   "model": self.vehicle_model,
                   "year": self.vehicle_year,
                   "license_plate": self.vehicle_license_plate,
                   "color": self.vehicle_color
               },
               "preferences": self.preferences,
               "status": self.status.value,
               "is_recurring": self.is_recurring,
               "recurring_schedule": self.recurring_schedule,
               "notes": self.notes,
               "created_at": self.created_at.isoformat(),
               "updated_at": self.updated_at.isoformat()
           }
   ```

3. PYDANTIC SCHEMAS (app/schemas/ride.py):
   
   ```python
   from pydantic import BaseModel, Field, field_validator
   from typing import Optional, Dict, Any
   from datetime import datetime, date
   from uuid import UUID
   from decimal import Decimal
   
   class LocationSchema(BaseModel):
       """Schema for location with address and coordinates"""
       address: str = Field(..., min_length=5, max_length=500)
       lat: float = Field(..., ge=-90, le=90, description="Latitude")
       lng: float = Field(..., ge=-180, le=180, description="Longitude")
   
   class VehicleSchema(BaseModel):
       """Schema for vehicle information"""
       make: str = Field(..., min_length=2, max_length=100)
       model: str = Field(..., min_length=2, max_length=100)
       year: int = Field(..., ge=1900, le=2030)
       license_plate: str = Field(..., min_length=2, max_length=20)
       color: Optional[str] = Field(None, max_length=50)
   
   class RideBase(BaseModel):
       """Base schema for ride with common fields"""
       origin: LocationSchema
       destination: LocationSchema
       departure_time: datetime
       available_seats: int = Field(..., ge=1, le=7)
       price_per_seat: Decimal = Field(..., ge=0, le=999.99)
       vehicle: VehicleSchema
       preferences: Optional[Dict[str, Any]] = None
       notes: Optional[str] = Field(None, max_length=1000)
       
       @field_validator('departure_time')
       @classmethod
       def validate_departure_time(cls, v: datetime) -> datetime:
           """Ensure departure time is at least 1 hour in the future"""
           from datetime import timezone, timedelta
           now = datetime.now(timezone.utc)
           min_time = now + timedelta(hours=1)
           
           if v < min_time:
               raise ValueError('Departure time must be at least 1 hour in the future')
           
           return v
       
       @field_validator('preferences')
       @classmethod
       def validate_preferences(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
           """Validate preference keys"""
           if v is None:
               return v
           
           allowed_keys = ['music', 'ac', 'stops', 'pets', 'smoking', 'luggage']
           for key in v.keys():
               if key not in allowed_keys:
                   raise ValueError(f'Invalid preference key: {key}')
           
           return v
   
   class RideCreate(RideBase):
       """Schema for creating a new ride"""
       is_recurring: bool = False
       recurring_schedule: Optional[Dict[str, Any]] = None
       
       @field_validator('recurring_schedule')
       @classmethod
       def validate_recurring_schedule(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
           """Validate recurring schedule if is_recurring is True"""
           is_recurring = info.data.get('is_recurring', False)
           
           if is_recurring and not v:
               raise ValueError('recurring_schedule required when is_recurring is True')
           
           if v and not is_recurring:
               raise ValueError('recurring_schedule provided but is_recurring is False')
           
           if v:
               required_keys = ['days', 'time']
               for key in required_keys:
                   if key not in v:
                       raise ValueError(f'recurring_schedule must include: {key}')
               
               valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
               for day in v.get('days', []):
                   if day.lower() not in valid_days:
                       raise ValueError(f'Invalid day: {day}')
           
           return v
   
   class RideUpdate(BaseModel):
       """Schema for updating a ride (all fields optional)"""
       origin: Optional[LocationSchema] = None
       destination: Optional[LocationSchema] = None
       departure_time: Optional[datetime] = None
       available_seats: Optional[int] = Field(None, ge=1, le=7)
       price_per_seat: Optional[Decimal] = Field(None, ge=0, le=999.99)
       vehicle: Optional[VehicleSchema] = None
       preferences: Optional[Dict[str, Any]] = None
       notes: Optional[str] = Field(None, max_length=1000)
   
   class RideResponse(RideBase):
       """Schema for ride API responses"""
       id: UUID
       driver_id: UUID
       status: str
       is_recurring: bool
       recurring_schedule: Optional[Dict[str, Any]]
       created_at: datetime
       updated_at: datetime
       driver_info: Optional[Dict[str, Any]] = None  # From user-service
       
       class Config:
           from_attributes = True
   
   class RideSearchParams(BaseModel):
       """Schema for ride search parameters"""
       origin_lat: Optional[float] = Field(None, ge=-90, le=90)
       origin_lng: Optional[float] = Field(None, ge=-180, le=180)
       destination_lat: Optional[float] = Field(None, ge=-90, le=90)
       destination_lng: Optional[float] = Field(None, ge=-180, le=180)
       departure_date: Optional[date] = None
       min_seats: int = Field(1, ge=1, le=7)
       max_price: Optional[Decimal] = Field(None, ge=0)
       proximity_km: float = Field(5.0, ge=0.1, le=50.0, description="Search radius in km")
   ```

4. GEOSPATIAL UTILITIES (app/utils/geo.py):
   
   ```python
   import math
   from typing import Tuple
   
   def haversine_distance(
       lat1: float, 
       lng1: float, 
       lat2: float, 
       lng2: float
   ) -> float:
       """
       Calculate the great circle distance between two points 
       on the earth using the Haversine formula.
       
       Args:
           lat1: Latitude of first point
           lng1: Longitude of first point
           lat2: Latitude of second point
           lng2: Longitude of second point
       
       Returns:
           Distance in kilometers
       
       Formula:
           a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlng/2)
           c = 2 * atan2(√a, √(1−a))
           d = R * c
           where R = Earth's radius (6371 km)
       """
       # Earth's radius in kilometers
       R = 6371.0
       
       # Convert degrees to radians
       lat1_rad = math.radians(lat1)
       lng1_rad = math.radians(lng1)
       lat2_rad = math.radians(lat2)
       lng2_rad = math.radians(lng2)
       
       # Differences
       dlat = lat2_rad - lat1_rad
       dlng = lng2_rad - lng1_rad
       
       # Haversine formula
       a = (
           math.sin(dlat / 2) ** 2 +
           math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
       )
       c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
       distance = R * c
       
       return distance
   
   def is_within_radius(
       point_lat: float,
       point_lng: float,
       center_lat: float,
       center_lng: float,
       radius_km: float
   ) -> bool:
       """
       Check if a point is within a given radius of a center point.
       
       Args:
           point_lat: Latitude of point to check
           point_lng: Longitude of point to check
           center_lat: Latitude of center point
           center_lng: Longitude of center point
           radius_km: Radius in kilometers
       
       Returns:
           True if point is within radius, False otherwise
       """
       distance = haversine_distance(point_lat, point_lng, center_lat, center_lng)
       return distance <= radius_km
   
   def calculate_bearing(
       lat1: float,
       lng1: float,
       lat2: float,
       lng2: float
   ) -> float:
       """
       Calculate the bearing (compass direction) from point 1 to point 2.
       
       Args:
           lat1: Latitude of starting point
           lng1: Longitude of starting point
           lat2: Latitude of ending point
           lng2: Longitude of ending point
       
       Returns:
           Bearing in degrees (0-360), where:
           - 0/360 = North
           - 90 = East
           - 180 = South
           - 270 = West
       """
       lat1_rad = math.radians(lat1)
       lng1_rad = math.radians(lng1)
       lat2_rad = math.radians(lat2)
       lng2_rad = math.radians(lng2)
       
       dlng = lng2_rad - lng1_rad
       
       x = math.sin(dlng) * math.cos(lat2_rad)
       y = (
           math.cos(lat1_rad) * math.sin(lat2_rad) -
           math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlng)
       )
       
       bearing_rad = math.atan2(x, y)
       bearing_deg = math.degrees(bearing_rad)
       
       # Normalize to 0-360
       bearing_deg = (bearing_deg + 360) % 360
       
       return bearing_deg
   
   def validate_coordinates(lat: float, lng: float) -> Tuple[bool, str]:
       """
       Validate latitude and longitude coordinates.
       
       Args:
           lat: Latitude
           lng: Longitude
       
       Returns:
           Tuple of (is_valid, error_message)
       """
       if not -90 <= lat <= 90:
           return False, f"Latitude must be between -90 and 90, got {lat}"
       
       if not -180 <= lng <= 180:
           return False, f"Longitude must be between -180 and 180, got {lng}"
       
       return True, ""
   ```

5. INTER-SERVICE COMMUNICATION (app/clients/user_client.py):
   
   ```python
   import httpx
   from typing import Optional, Dict, Any
   from uuid import UUID
   import logging
   from app.core.config import settings
   
   logger = logging.getLogger(__name__)
   
   class UserServiceClient:
       """
       Client for communicating with user-service
       Handles user verification and profile retrieval
       """
       
       def __init__(self):
           self.base_url = settings.USER_SERVICE_URL
           self.timeout = httpx.Timeout(10.0, connect=5.0)
       
       async def get_user(self, user_id: UUID) -> Optional[Dict[str, Any]]:
           """
           Get user information from user-service
           
           Args:
               user_id: UUID of user to fetch
           
           Returns:
               User data dictionary or None if not found
           
           Raises:
               Exception if service is unavailable
           """
           try:
               async with httpx.AsyncClient(timeout=self.timeout) as client:
                   response = await client.get(
                       f"{self.base_url}/api/v1/users/{user_id}"
                   )
                   
                   if response.status_code == 200:
                       return response.json()
                   elif response.status_code == 404:
                       logger.warning(f"User not found: {user_id}")
                       return None
                   else:
                       logger.error(
                           f"Error fetching user {user_id}: "
                           f"Status {response.status_code}"
                       )
                       return None
           
           except httpx.TimeoutException:
               logger.error(f"Timeout fetching user {user_id}")
               raise Exception("User service timeout")
           except httpx.RequestError as e:
               logger.error(f"Error connecting to user service: {e}")
               raise Exception("User service unavailable")
       
       async def verify_driver_license(self, user_id: UUID) -> bool:
           """
           Check if user has verified driver's license
           
           Args:
               user_id: UUID of user to check
           
           Returns:
               True if license verified, False otherwise
           """
           user = await self.get_user(user_id)
           if not user:
               return False
           
           return user.get('driver_license_verified', False)
       
       async def get_user_rating(self, user_id: UUID) -> Optional[float]:
           """
           Get user's rating
           
           Args:
               user_id: UUID of user
           
           Returns:
               User rating or None
           """
           user = await self.get_user(user_id)
           if not user:
               return None
           
           return user.get('rating')
   
   # Global client instance
   user_client = UserServiceClient()
   ```

6. RIDE SERVICE (app/services/ride_service.py):
   
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, and_, or_, func
   from sqlalchemy.exc import SQLAlchemyError
   from typing import List, Optional
   from uuid import UUID
   from datetime import datetime, timezone, date
   import logging
   
   from app.models.ride import Ride, RideStatus
   from app.schemas.ride import RideCreate, RideUpdate, RideSearchParams
   from app.clients.user_client import user_client
   from app.utils.geo import haversine_distance, is_within_radius
   from app.core.exceptions import (
       RideNotFoundException,
       UnauthorizedException,
       InvalidRideDataException
   )
   
   logger = logging.getLogger(__name__)
   
   class RideService:
       """Service for ride CRUD operations and search"""
       
       async def create_ride(
           self,
           ride_data: RideCreate,
           driver_id: UUID,
           db: AsyncSession
       ) -> Ride:
           """
           Create a new ride
           
           Args:
               ride_data: Ride creation data
               driver_id: UUID of driver creating the ride
               db: Database session
           
           Returns:
               Created Ride object
           
           Raises:
               InvalidRideDataException: If driver not verified
           """
           # Verify driver exists and has verified license
           driver = await user_client.get_user(driver_id)
           if not driver:
               raise InvalidRideDataException("Driver not found")
           
           if not driver.get('driver_license_verified', False):
               raise InvalidRideDataException(
                   "Driver must have verified license to post rides"
               )
           
           # Create ride
           ride = Ride(
               driver_id=driver_id,
               origin_address=ride_data.origin.address,
               origin_lat=ride_data.origin.lat,
               origin_lng=ride_data.origin.lng,
               destination_address=ride_data.destination.address,
               destination_lat=ride_data.destination.lat,
               destination_lng=ride_data.destination.lng,
               departure_time=ride_data.departure_time,
               available_seats=ride_data.available_seats,
               price_per_seat=ride_data.price_per_seat,
               vehicle_make=ride_data.vehicle.make,
               vehicle_model=ride_data.vehicle.model,
               vehicle_year=ride_data.vehicle.year,
               vehicle_license_plate=ride_data.vehicle.license_plate,
               vehicle_color=ride_data.vehicle.color,
               preferences=ride_data.preferences or {},
               notes=ride_data.notes,
               is_recurring=ride_data.is_recurring,
               recurring_schedule=ride_data.recurring_schedule,
               status=RideStatus.ACTIVE
           )
           
           try:
               db.add(ride)
               await db.commit()
               await db.refresh(ride)
               
               logger.info(f"Created ride {ride.id} by driver {driver_id}")
               return ride
           
           except SQLAlchemyError as e:
               await db.rollback()
               logger.error(f"Error creating ride: {e}")
               raise
       
       async def get_ride_by_id(
           self,
           ride_id: UUID,
           db: AsyncSession
       ) -> Optional[Ride]:
           """Get ride by ID"""
           result = await db.execute(
               select(Ride).where(Ride.id == ride_id)
           )
           return result.scalar_one_or_none()
       
       async def get_rides_by_driver(
           self,
           driver_id: UUID,
           db: AsyncSession,
           status: Optional[str] = None
       ) -> List[Ride]:
           """
           Get all rides for a driver
           
           Args:
               driver_id: Driver's user ID
               db: Database session
               status: Optional status filter
           
           Returns:
               List of Ride objects
           """
           query = select(Ride).where(Ride.driver_id == driver_id)
           
           if status:
               query = query.where(Ride.status == status)
           
           query = query.order_by(Ride.departure_time.desc())
           
           result = await db.execute(query)
           return result.scalars().all()
       
       async def search_rides(
           self,
           params: RideSearchParams,
           db: AsyncSession
       ) -> List[Ride]:
           """
           Search for rides with filters
           
           Args:
               params: Search parameters
               db: Database session
           
           Returns:
               List of matching Ride objects
           """
           # Base query: active rides only
           query = select(Ride).where(Ride.status == RideStatus.ACTIVE)
           
           # Filter by departure date if provided
           if params.departure_date:
               start_of_day = datetime.combine(
                   params.departure_date,
                   datetime.min.time()
               ).replace(tzinfo=timezone.utc)
               end_of_day = datetime.combine(
                   params.departure_date,
                   datetime.max.time()
               ).replace(tzinfo=timezone.utc)
               
               query = query.where(
                   and_(
                       Ride.departure_time >= start_of_day,
                       Ride.departure_time <= end_of_day
                   )
               )
           
           # Filter by available seats
           query = query.where(Ride.available_seats >= params.min_seats)
           
           # Filter by price
           if params.max_price is not None:
               query = query.where(Ride.price_per_seat <= params.max_price)
           
           # Order by departure time (earliest first)
           query = query.order_by(Ride.departure_time.asc())
           
           # Limit results
           query = query.limit(50)
           
           result = await db.execute(query)
           rides = result.scalars().all()
           
           # Apply geospatial filters in Python
           # (In production, consider PostGIS for database-level geospatial queries)
           filtered_rides = []
           
           for ride in rides:
               # Check origin proximity if provided
               if params.origin_lat is not None and params.origin_lng is not None:
                   if not is_within_radius(
                       ride.origin_lat,
                       ride.origin_lng,
                       params.origin_lat,
                       params.origin_lng,
                       params.proximity_km
                   ):
                       continue
               
               # Check destination proximity if provided
               if params.destination_lat is not None and params.destination_lng is not None:
                   if not is_within_radius(
                       ride.destination_lat,
                       ride.destination_lng,
                       params.destination_lat,
                       params.destination_lng,
                       params.proximity_km
                   ):
                       continue
               
               filtered_rides.append(ride)
           
           logger.info(f"Found {len(filtered_rides)} rides matching search criteria")
           return filtered_rides
       
       async def update_ride(
           self,
           ride_id: UUID,
           ride_data: RideUpdate,
           driver_id: UUID,
           db: AsyncSession
       ) -> Ride:
           """
           Update ride (only by owner)
           
           Args:
               ride_id: Ride ID to update
               ride_data: Update data
               driver_id: Driver ID (for authorization)
               db: Database session
           
           Returns:
               Updated Ride object
           
           Raises:
               RideNotFoundException: If ride not found
               UnauthorizedException: If not ride owner
           """
           ride = await self.get_ride_by_id(ride_id, db)
           
           if not ride:
               raise RideNotFoundException(f"Ride {ride_id} not found")
           
           if ride.driver_id != driver_id:
               raise UnauthorizedException("Not authorized to update this ride")
           
           # Update fields if provided
           if ride_data.origin:
               ride.origin_address = ride_data.origin.address
               ride.origin_lat = ride_data.origin.lat
               ride.origin_lng = ride_data.origin.lng
           
           if ride_data.destination:
               ride.destination_address = ride_data.destination.address
               ride.destination_lat = ride_data.destination.lat
               ride.destination_lng = ride_data.destination.lng
           
           if ride_data.departure_time:
               ride.departure_time = ride_data.departure_time
           
           if ride_data.available_seats is not None:
               ride.available_seats = ride_data.available_seats
           
           if ride_data.price_per_seat is not None:
               ride.price_per_seat = ride_data.price_per_seat
           
           if ride_data.vehicle:
               ride.vehicle_make = ride_data.vehicle.make
               ride.vehicle_model = ride_data.vehicle.model
               ride.vehicle_year = ride_data.vehicle.year
               ride.vehicle_license_plate = ride_data.vehicle.license_plate
               ride.vehicle_color = ride_data.vehicle.color
           
           if ride_data.preferences is not None:
               ride.preferences = ride_data.preferences
           
           if ride_data.notes is not None:
               ride.notes = ride_data.notes
           
           try:
               await db.commit()
               await db.refresh(ride)
               
               logger.info(f"Updated ride {ride_id}")
               return ride
           
           except SQLAlchemyError as e:
               await db.rollback()
               logger.error(f"Error updating ride: {e}")
               raise
       
       async def delete_ride(
           self,
           ride_id: UUID,
           driver_id: UUID,
           db: AsyncSession
       ) -> None:
           """
           Delete ride (set status to cancelled)
           
           Args:
               ride_id: Ride ID to delete
               driver_id: Driver ID (for authorization)
               db: Database session
           
           Raises:
               RideNotFoundException: If ride not found
               UnauthorizedException: If not ride owner
           """
           ride = await self.get_ride_by_id(ride_id, db)
           
           if not ride:
               raise RideNotFoundException(f"Ride {ride_id} not found")
           
           if ride.driver_id != driver_id:
               raise UnauthorizedException("Not authorized to delete this ride")
           
           # Set status to cancelled instead of deleting
           ride.status = RideStatus.CANCELLED
           
           try:
               await db.commit()
               logger.info(f"Cancelled ride {ride_id}")
           
           except SQLAlchemyError as e:
               await db.rollback()
               logger.error(f"Error cancelling ride: {e}")
               raise
       
       async def get_available_rides(
           self,
           db: AsyncSession,
           limit: int = 20
       ) -> List[Ride]:
           """
           Get recent available rides for homepage feed
           
           Args:
               db: Database session
               limit: Max number of rides to return
           
           Returns:
               List of Ride objects
           """
           query = (
               select(Ride)
               .where(Ride.status == RideStatus.ACTIVE)
               .where(Ride.departure_time > datetime.now(timezone.utc))
               .order_by(Ride.created_at.desc())
               .limit(limit)
           )
           
           result = await db.execute(query)
           return result.scalars().all()
   
   # Service instance
   ride_service = RideService()
   ```

7. API ROUTES (app/api/routes/rides.py):
   
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status, Query
   from sqlalchemy.ext.asyncio import AsyncSession
   from typing import List, Optional
   from uuid import UUID
   from datetime import date
   from decimal import Decimal
   
   from app.core.database import get_db
   from app.schemas.ride import RideCreate, RideUpdate, RideResponse, RideSearchParams
   from app.services.ride_service import ride_service
   from app.clients.user_client import user_client
   from app.core.exceptions import (
       RideNotFoundException,
       UnauthorizedException,
       InvalidRideDataException
   )
   
   router = APIRouter()
   
   # Mock authentication dependency (replace with actual JWT validation)
   async def get_current_user_id() -> UUID:
       """Mock current user - replace with actual JWT validation"""
       # For testing, return a fixed UUID
       # In production, extract from JWT token
       return UUID("12345678-1234-5678-1234-567812345678")
   
   @router.post(
       "",
       response_model=RideResponse,
       status_code=status.HTTP_201_CREATED,
       summary="Create a new ride",
       description="Post a new ride. Driver must have verified license."
   )
   async def create_ride(
       ride_data: RideCreate,
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """Create new ride (protected route)"""
       try:
           ride = await ride_service.create_ride(ride_data, current_user_id, db)
           
           # Get driver info
           driver = await user_client.get_user(ride.driver_id)
           
           response = RideResponse.model_validate(ride)
           response.driver_info = driver
           
           return response
       
       except InvalidRideDataException as e:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail=str(e)
           )
   
   @router.get(
       "/{ride_id}",
       response_model=RideResponse,
       summary="Get ride by ID",
       description="Get detailed information about a specific ride"
   )
   async def get_ride(
       ride_id: UUID,
       db: AsyncSession = Depends(get_db)
   ):
       """Get ride by ID (public route)"""
       ride = await ride_service.get_ride_by_id(ride_id, db)
       
       if not ride:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Ride {ride_id} not found"
           )
       
       # Get driver info
       driver = await user_client.get_user(ride.driver_id)
       
       response = RideResponse.model_validate(ride)
       response.driver_info = driver
       
       return response
   
   @router.put(
       "/{ride_id}",
       response_model=RideResponse,
       summary="Update ride",
       description="Update ride details (owner only)"
   )
   async def update_ride(
       ride_id: UUID,
       ride_data: RideUpdate,
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """Update ride (protected route)"""
       try:
           ride = await ride_service.update_ride(
               ride_id,
               ride_data,
               current_user_id,
               db
           )
           
           driver = await user_client.get_user(ride.driver_id)
           
           response = RideResponse.model_validate(ride)
           response.driver_info = driver
           
           return response
       
       except RideNotFoundException as e:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=str(e)
           )
       except UnauthorizedException as e:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail=str(e)
           )
   
   @router.delete(
       "/{ride_id}",
       status_code=status.HTTP_204_NO_CONTENT,
       summary="Delete ride",
       description="Cancel ride (owner only)"
   )
   async def delete_ride(
       ride_id: UUID,
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """Delete/cancel ride (protected route)"""
       try:
           await ride_service.delete_ride(ride_id, current_user_id, db)
       
       except RideNotFoundException as e:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=str(e)
           )
       except UnauthorizedException as e:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail=str(e)
           )
   
   @router.get(
       "",
       response_model=List[RideResponse],
       summary="Search rides",
       description="Search for rides with various filters"
   )
   async def search_rides(
       origin_lat: Optional[float] = Query(None, ge=-90, le=90),
       origin_lng: Optional[float] = Query(None, ge=-180, le=180),
       destination_lat: Optional[float] = Query(None, ge=-90, le=90),
       destination_lng: Optional[float] = Query(None, ge=-180, le=180),
       departure_date: Optional[date] = None,
       min_seats: int = Query(1, ge=1, le=7),
       max_price: Optional[Decimal] = Query(None, ge=0),
       proximity_km: float = Query(5.0, ge=0.1, le=50.0),
       db: AsyncSession = Depends(get_db)
   ):
       """Search rides (public route)"""
       search_params = RideSearchParams(
           origin_lat=origin_lat,
           origin_lng=origin_lng,
           destination_lat=destination_lat,
           destination_lng=destination_lng,
           departure_date=departure_date,
           min_seats=min_seats,
           max_price=max_price,
           proximity_km=proximity_km
       )
       
       rides = await ride_service.search_rides(search_params, db)
       
       # Enrich with driver info
       responses = []
       for ride in rides:
           driver = await user_client.get_user(ride.driver_id)
           response = RideResponse.model_validate(ride)
           response.driver_info = driver
           responses.append(response)
       
       return responses
   
   @router.get(
       "/driver/me",
       response_model=List[RideResponse],
       summary="Get my rides",
       description="Get all rides posted by current user"
   )
   async def get_my_rides(
       status: Optional[str] = Query(None, description="Filter by status"),
       current_user_id: UUID = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_db)
   ):
       """Get current driver's rides (protected route)"""
       rides = await ride_service.get_rides_by_driver(
           current_user_id,
           db,
           status
       )
       
       driver = await user_client.get_user(current_user_id)
       
       responses = []
       for ride in rides:
           response = RideResponse.model_validate(ride)
           response.driver_info = driver
           responses.append(response)
       
       return responses
   
   @router.get(
       "/feed",
       response_model=List[RideResponse],
       summary="Get ride feed",
       description="Get recent available rides for homepage"
   )
   async def get_ride_feed(
       limit: int = Query(20, ge=1, le=50),
       db: AsyncSession = Depends(get_db)
   ):
       """Get ride feed (public route)"""
       rides = await ride_service.get_available_rides(db, limit)
       
       # Enrich with driver info
       responses = []
       for ride in rides:
           driver = await user_client.get_user(ride.driver_id)
           response = RideResponse.model_validate(ride)
           response.driver_info = driver
           responses.append(response)
       
       return responses
   ```



8. CUSTOM EXCEPTIONS (app/core/exceptions.py):
   Create exceptions:
   - RideNotFoundException
   - UnauthorizedException  
   - InvalidRideDataException
   - RideHasBookingsException (for later)

9. DOCKER CONFIGURATION:
   Update backend/docker-compose.yml:
   ```yaml
   ride-service:
     build: ./services/ride-service
     ports: ["8002:8000"]
     environment:
       - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare
       - USER_SERVICE_URL=http://user-service:8000
       - REDIS_URL=redis://redis:6379/0
     depends_on: [postgres, redis, user-service]
   ```

10. ALEMBIC SETUP:
    - Initialize Alembic: `alembic init alembic`
    - Configure alembic.ini and env.py for async
    - Create migration: `alembic revision --autogenerate -m "Create rides table"`
    - Migration should create rides table with all columns, indexes, enums

11. CONFIGURATION (app/core/config.py):
    Add settings:
    - USER_SERVICE_URL: str
    - Same database/redis settings as user-service

12. MAIN APP (app/main.py):
    - Setup FastAPI with CORS
    - Include health router and rides router
    - Add startup/shutdown events
    - Similar to user-service structure

13. REQUIREMENTS.txt:
    Same as user-service plus:
    - httpx==0.25.2 (for inter-service calls)

14. GENERATE LEARNING DOCUMENTATION:
    Create: docs/learning/03-microservice-communication.md
    
    Cover (10-15 pages):
    - Microservices communication patterns (sync/async)
    - RESTful API design principles
    - Database relationships in microservices
    - Inter-service communication with HTTP
    - Geospatial data and calculations
    - Search and filtering best practices
    - DateTime handling (UTC, timezones)
    - Error handling across services
    - Circuit breaker pattern (future)
    - Code examples for each concept

15. TESTING (tests/test_rides.py):
    Create tests:
    - test_create_ride_success
    - test_create_ride_no_license (should fail)
    - test_create_ride_past_time (should fail)
    - test_get_ride_by_id
    - test_update_ride_owner (success)
    - test_update_ride_not_owner (403)
    - test_delete_ride
    - test_search_by_origin_proximity
    - test_search_by_destination_proximity
    - test_search_by_date
    - test_search_by_price
    - test_get_driver_rides
    - test_haversine_distance_calculation

16. POSTMAN COLLECTION UPDATE:
    Add "Rides" folder with requests:
    - Create Ride (with auth token from user login)
    - Create Ride Invalid Data (various validation errors)
    - Get Ride by ID
    - Update Ride (owner)
    - Update Ride (not owner - should fail 403)
    - Delete Ride
    - Search Rides (no filters)
    - Search Rides (by origin)
    - Search Rides (by destination)
    - Search Rides (by date)
    - Search Rides (by price)
    - Get My Rides (as driver)
    - Get Ride Feed

17. README.md:
    Document API endpoints, setup instructions, testing

CODE QUALITY & VERIFICATION:
- Use async/await throughout
- Type hints on all functions
- Comprehensive docstrings
- Error handling with try/except
- Logging at appropriate levels
- Input validation with Pydantic
- Database transactions properly managed

VERIFICATION CHECKLIST:
- [ ] Ride-service starts on port 8002
- [ ] Can create ride (authenticated user with license)
- [ ] Can't create ride without license
- [ ] Can't create ride with past departure time
- [ ] Can get ride by ID
- [ ] Can update own ride
- [ ] Can't update others' rides (403)
- [ ] Can delete own ride
- [ ] Search by origin works (proximity filter)
- [ ] Search by destination works
- [ ] Search by date works
- [ ] Haversine distance calculation accurate
- [ ] Inter-service call to user-service works
- [ ] Handles user-service timeout gracefully
- [ ] All tests pass
- [ ] Migrations run successfully

```

---

<a name="section-4"></a>
# SECTION 4: Google Maps Integration

## Learning Objectives
- Integrate third-party APIs
- Google Maps API setup and configuration
- Geocoding (address → coordinates)
- Reverse geocoding (coordinates → address)
- Directions API for routes
- Distance Matrix API
- API key security and rate limiting
- Caching strategies with Redis

## Technologies
- Google Maps Platform APIs
- googlemaps Python client
- Redis for caching
- API key management
- Rate limiting

## Prerequisites
- Sections 1-3 completed ✅
- Google Cloud account
- Credit card for Google Cloud (stays within free $200/month)
- Understanding of HTTP APIs
- Redis running

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Google Maps Integration

CONTEXT:
Sections 1-3 completed. User and ride services working.
Integrating Google Maps APIs for geocoding, directions, and distance calculations.
Section 4 of 13.

GOAL:
Integrate Google Maps Platform APIs to enable:
- Address autocomplete
- Address to coordinates conversion (geocoding)
- Coordinates to address conversion (reverse geocoding)
- Route calculation with distance/duration
- Distance matrix for multiple origins/destinations
All with caching and rate limiting.

DETAILED REQUIREMENTS:

1. GOOGLE MAPS SETUP (Manual Steps):
   - Go to console.cloud.google.com
   - Create new project: "SJSU RideShare"
   - Enable APIs:
     * Maps JavaScript API
     * Places API
     * Geocoding API
     * Directions API
     * Distance Matrix API
   - Create API key
   - Restrict API key:
     * Application restrictions: HTTP referrers
     * API restrictions: Select enabled APIs only
   - Enable billing (required, but stays within $200 free credit)
   - Set budget alert at $50

2. CONFIGURATION UPDATE:
   Add to both user-service and ride-service config:
   ```python
   # Google Maps Configuration
   GOOGLE_MAPS_API_KEY: str
   GOOGLE_MAPS_ENABLED: bool = True
   GOOGLE_MAPS_CACHE_TTL_GEOCODE: int = 2592000  # 30 days
   GOOGLE_MAPS_CACHE_TTL_ROUTE: int = 3600  # 1 hour
   ```

3. SHARED UTILITIES:
   Create: backend/shared/utils/maps_client.py
   
   Functions to implement:
   
   A. geocode_address(address: str) -> dict:
      - Convert address to lat/lng
      - Return: {"lat": float, "lng": float, "formatted_address": str}
      - Handle errors: invalid address, API errors
      - Cache result in Redis (30 days)
   
   B. reverse_geocode(lat: float, lng: float) -> str:
      - Convert coordinates to address
      - Return formatted address string
      - Cache result (30 days)
   
   C. autocomplete_places(input_text: str, location_bias: tuple = None) -> List[dict]:
      - Return address suggestions
      - Bias towards SJSU area: (37.3352, -121.8811)
      - Return list with place_id and description
   
   D. get_place_details(place_id: str) -> dict:
      - Get full details from place_id
      - Return address, components, coordinates
   
   E. calculate_route(origin: dict, destination: dict, waypoints: List = None) -> dict:
      - Calculate route between points
      - Return:
        * distance: {"text": "10.5 mi", "value": 16898}  # meters
        * duration: {"text": "20 mins", "value": 1200}  # seconds
        * polyline: encoded string for map display
        * steps: turn-by-turn directions (optional)
      - Cache result (1 hour)
   
   F. calculate_distance_matrix(origins: List[dict], destinations: List[dict]) -> dict:
      - Batch calculate distances
      - Useful for finding closest pickup
      - Return matrix of distances/durations
      - Cache (1 hour)
   
   G. validate_coordinates(lat: float, lng: float) -> bool:
      - Check lat: -90 to 90
      - Check lng: -180 to 180

4. CACHING IMPLEMENTATION:
   Create: backend/shared/utils/cache_manager.py
   
   ```python
   class CacheManager:
       def __init__(self, redis_client):
           self.redis = redis_client
       
       async def get_cached(self, key: str) -> Optional[dict]:
           # Get from Redis, return parsed JSON or None
       
       async def set_cached(self, key: str, value: dict, ttl: int):
           # Store in Redis with TTL
       
       def generate_cache_key(self, operation: str, *args) -> str:
           # Generate consistent cache key
           # Example: "geocode:123_main_street_san_jose_ca"
   ```

5. UPDATE RIDE CREATION:
   Modify ride-service create_ride:
   
   - If address provided but no coordinates:
     * Call geocode_address()
     * Store both address and coordinates
   
   - If coordinates provided but no address:
     * Call reverse_geocode()
     * Store both
   
   - Validate coordinates with validate_coordinates()

6. ENHANCED RIDE SEARCH:
   Add to ride-service:
   
   POST /api/v1/rides/match-route:
   - Accept passenger origin and destination
   - Calculate route for passenger journey
   - Find rides where:
     * Driver origin near passenger origin
     * Driver destination near passenger destination  
     * Calculate detour for driver
   - Use Distance Matrix API
   - Filter rides with < 10 min detour
   - Return sorted by detour time

7. ROUTE PREVIEW ENDPOINT:
   Add to ride-service:
   
   POST /api/v1/rides/{ride_id}/preview-route:
   - Calculate full route with directions
   - Return distance, duration, polyline
   - Include turn-by-turn steps
   - Cache for 1 hour

8. PICKUP LOCATION SUGGESTIONS:
   Add to ride-service:
   
   POST /api/v1/rides/{ride_id}/suggest-pickup:
   Request: {"passenger_location": {"lat": x, "lng": y}}
   - Find optimal pickup point on driver's route
   - Calculate detour
   - Return suggested location with detour info

9. ERROR HANDLING:
   Handle Google Maps API errors:
   - ZERO_RESULTS: "Address not found"
   - OVER_QUERY_LIMIT: "Service temporarily unavailable"
   - REQUEST_DENIED: Log error, alert admin
   - INVALID_REQUEST: Return 400 with details
   - UNKNOWN_ERROR: Retry once, then return cached or estimate
   
   Fallback strategies:
   - Use cached results if available
   - Use Haversine for distance if API fails
   - Graceful degradation

10. RATE LIMITING:
    Track API usage:
    - Log each API call
    - Store daily counter in Redis
    - Alert if approaching limits (80% of quota)
    - Implement exponential backoff on errors

11. COST OPTIMIZATION:
    - Cache aggressively (30 days for addresses, 1 hour for routes)
    - Batch Distance Matrix requests
    - Use Haversine for initial filtering
    - Only call Google Maps for final results
    - Monitor usage with logging
    
    Expected costs for 100 users:
    - Geocoding: ~200 requests/day → $0.40 (with cache)
    - Directions: ~50 requests/day → $0.25
    - Distance Matrix: ~100 requests/day → $0.50
    - Total: ~$1.15/day = $35/month (well within $200 credit)

12. ENVIRONMENT VARIABLES:
    Update .env.example:
    ```
    GOOGLE_MAPS_API_KEY=your_api_key_here
    GOOGLE_MAPS_ENABLED=True
    ```

13. REQUIREMENTS UPDATE:
    Add to requirements.txt:
    ```
    googlemaps==4.10.0
    ```

14. GENERATE LEARNING DOCUMENTATION:
    Create: docs/learning/04-google-maps-integration.md
    
    Cover (15-20 pages):
    1. Google Maps Platform Overview
       - Available APIs and pricing
       - Free tier ($200 credit)
       - Cost structure
    
    2. API Key Management
       - Creating and securing keys
       - Restrictions (HTTP referrers, IP, API)
       - Key rotation strategy
    
    3. Geocoding Deep Dive
       - How geocoding works
       - Accuracy levels
       - Address components
       - Common issues and solutions
    
    4. Places API
       - Autocomplete implementation
       - Place details
       - Search vs autocomplete
    
    5. Directions API
       - Route calculation
       - Alternative routes
       - Waypoints
       - Polyline encoding/decoding
    
    6. Distance Matrix API
       - Use cases
       - Batch requests
       - Cost optimization
    
    7. Caching Strategies
       - What to cache and for how long
       - Cache invalidation
       - Cache keys design
       - Redis implementation
    
    8. Rate Limiting
       - Google's limits
       - Monitoring usage
       - Graceful degradation
    
    9. Cost Optimization Techniques
       - Request minimization
       - Caching
       - Batching
       - Alternatives
    
    10. Error Handling
        - Common errors
        - Retry strategies
        - Fallback mechanisms
    
    11. Security Best Practices
        - Never expose API key client-side
        - Use environment variables
        - Implement backend proxy
        - Monitor for abuse
    
    12. Code examples for each API

15. TESTING (tests/test_maps.py):
    Create tests (mock Google Maps API):
    - test_geocode_address_success
    - test_geocode_invalid_address
    - test_reverse_geocode
    - test_autocomplete_places
    - test_calculate_route
    - test_distance_matrix
    - test_caching_works
    - test_cache_expiration
    - test_error_handling
    - test_rate_limit_tracking

16. POSTMAN COLLECTION UPDATE:
    Add "Maps Integration" folder:
    - Geocode Address
    - Reverse Geocode
    - Autocomplete Places
    - Get Place Details
    - Calculate Route
    - Distance Matrix
    - Search Rides with Route Match
    - Preview Route
    - Suggest Pickup Location

17. SETUP INSTRUCTIONS:
    Document in README:
    - How to get Google Maps API key
    - How to configure restrictions
    - How to monitor usage
    - Cost expectations

SECURITY REQUIREMENTS:
- API key in environment variables ONLY
- Never commit API key to Git
- Set proper restrictions on API key
- Monitor usage for anomalies
- Rotate keys periodically (quarterly)

VERIFICATION CHECKLIST:
- [ ] Google Cloud project created
- [ ] All APIs enabled
- [ ] API key generated and restricted
- [ ] API key in .env (not in code)
- [ ] Can geocode addresses
- [ ] Invalid addresses handled gracefully
- [ ] Can reverse geocode
- [ ] Autocomplete returns suggestions
- [ ] Route calculation works
- [ ] Distance matrix works
- [ ] Results cached in Redis
- [ ] Cache hit rate > 80%
- [ ] Second request uses cache (verify in logs)
- [ ] Error handling works
- [ ] Graceful degradation on API failure
- [ ] Usage logged
- [ ] Staying within budget ($5-10/month)
- [ ] All tests pass

Please generate all files following the requirements above.
Include comprehensive error handling, caching, and documentation.
```

---

## TESTING CHECKLIST - SECTION 3

### Prerequisites
- [ ] Sections 1-2 completed
- [ ] User-service running on 8001
- [ ] Can create and login users
- [ ] JWT tokens working

### Setup
- [ ] Ride-service directory created
- [ ] All files in correct structure
- [ ] Dockerfile created
- [ ] docker-compose.yml updated
- [ ] Port 8002 configured

### Database
- [ ] Alembic initialized
- [ ] Migration created
- [ ] Run: `alembic upgrade head`
- [ ] Rides table exists in database
- [ ] Check: `\d rides` shows all columns
- [ ] Indexes created
- [ ] Enum types created

### Service Startup
- [ ] `docker-compose up -d ride-service`
- [ ] No errors in logs
- [ ] Health endpoint: http://localhost:8002/health
- [ ] API docs: http://localhost:8002/docs

### Create Ride (Valid)
Request:
```json
POST http://localhost:8002/api/v1/rides
Authorization: Bearer {token}

{
  "origin": {
    "address": "San Jose State University",
    "lat": 37.3352,
    "lng": -121.8811
  },
  "destination": {
    "address": "San Francisco Airport",
    "lat": 37.6213,
    "lng": -122.3790
  },
  "departure_time": "2024-12-25T10:00:00Z",
  "available_seats": 3,
  "price_per_seat": 15.00,
  "vehicle": {
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "license_plate": "ABC123",
    "color": "Silver"
  },
  "preferences": {
    "music": true,
    "ac": true,
    "stops": false
  },
  "notes": "Leaving from SJSU campus"
}
```
- [ ] Returns 201
- [ ] Ride ID returned
- [ ] Driver info included

### Validation Tests
- [ ] Past departure time: 422 error
- [ ] Seats > 7: 422 error
- [ ] Invalid coordinates: 422 error
- [ ] No driver license: 400 error

### Search Tests
- [ ] Search with no filters: returns rides
- [ ] Search by origin (proximity): works
- [ ] Search by destination (proximity): works
- [ ] Search by date: works
- [ ] Search by price: works
- [ ] Search by seats: works

### CRUD Operations
- [ ] Get ride by ID: 200
- [ ] Update ride (owner): 200
- [ ] Update ride (not owner): 403
- [ ] Delete ride (owner): 204
- [ ] Get my rides: returns driver's rides

### Geospatial
- [ ] Haversine calculation accurate
- [ ] Proximity filter works
- [ ] Within radius: included
- [ ] Outside radius: excluded

### Inter-Service
- [ ] Calls user-service successfully
- [ ] Gets driver info
- [ ] Handles user-service down

### Learning
- [ ] Read 03-microservice-communication.md
- [ ] Understand REST API design
- [ ] Understand geospatial calculations
- [ ] Understand inter-service communication

---

## TESTING CHECKLIST - SECTION 4

### Google Cloud Setup
- [ ] Project created
- [ ] Billing enabled
- [ ] Budget alert set ($50)
- [ ] APIs enabled (5 APIs)
- [ ] API key created
- [ ] Restrictions configured

### Configuration
- [ ] API key in .env
- [ ] API key NOT in code
- [ ] API key NOT in Git
- [ ] googlemaps package installed

### Geocoding
```bash
# Test geocode
POST /api/v1/geocode
{
  "address": "San Jose State University, San Jose, CA"
}
```
- [ ] Returns coordinates
- [ ] Returns formatted address
- [ ] Result cached in Redis
- [ ] Second call uses cache (check logs)

### Reverse Geocoding
```bash
POST /api/v1/reverse-geocode
{
  "lat": 37.3352,
  "lng": -121.8811
}
```
- [ ] Returns address
- [ ] Cached

### Autocomplete
```bash
GET /api/v1/autocomplete?input=San Jose State
```
- [ ] Returns suggestions
- [ ] Includes place_ids
- [ ] Biased towards SJSU area

### Route Calculation
```bash
POST /api/v1/calculate-route
{
  "origin": {"lat": 37.3352, "lng": -121.8811},
  "destination": {"lat": 37.6213, "lng": -122.3790}
}
```
- [ ] Returns distance
- [ ] Returns duration
- [ ] Returns polyline
- [ ] Cached

### Distance Matrix
```bash
POST /api/v1/distance-matrix
{
  "origins": [{"lat": x1, "lng": y1}, {"lat": x2, "lng": y2}],
  "destinations": [{"lat": x3, "lng": y3}]
}
```
- [ ] Returns matrix
- [ ] All combinations calculated

### Integration with Rides
- [ ] Create ride with address only: geocodes
- [ ] Create ride with coordinates only: reverse geocodes
- [ ] Route preview works
- [ ] Pickup suggestions work

### Caching
- [ ] First request hits API
- [ ] Second request uses cache
- [ ] Cache key format correct
- [ ] TTL working (check Redis)
- [ ] Cache hit rate > 80%

### Error Handling
- [ ] Invalid address: proper error
- [ ] API key error: logged
- [ ] Rate limit: graceful
- [ ] Timeout: falls back to Haversine

### Cost Monitoring
- [ ] Usage logged
- [ ] Daily counter in Redis
- [ ] Check Google Cloud Console usage
- [ ] Staying under $10/month

### Learning
- [ ] Read 04-google-maps-integration.md
- [ ] Understand geocoding
- [ ] Understand API costs
- [ ] Understand caching strategy

---

## COMPLETION SIGN-OFF

**Section 3:**
- [ ] All tests passing
- [ ] Service running on 8002
- [ ] Inter-service communication working
- [ ] Ready for Section 4

**Section 4:**
- [ ] Google Maps integrated
- [ ] All APIs working
- [ ] Caching implemented
- [ ] Costs monitored
- [ ] Ready for Section 5

**Date Completed:** _______________
**Issues Encountered:** _______________
**Notes:** _______________

