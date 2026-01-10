# SJSU RideShare Development Guide
## Section 13: SJSU-Specific Features & Launch Preparation

**Version:** 1.0
**Duration:** Week 13-14 (7-10 days)
**Focus:** Campus-Specific Features, Testing, Deployment, Beta Launch

---

# TABLE OF CONTENTS

1. [SJSU-Specific Features](#sjsu-features)
2. [Testing & Quality Assurance](#testing)
3. [Deployment & Production Setup](#deployment)
4. [Beta Launch Preparation](#launch)
5. [Post-Launch Monitoring](#monitoring)

---

<a name="sjsu-features"></a>
# PART 1: SJSU-SPECIFIC FEATURES

## Why These Features Are Your Competitive Moat

These features are **impossible for Uber/Lyft to replicate** and create strong network effects at SJSU:
- ✅ SJSU email verification (@sjsu.edu)
- ✅ Campus building quick selection
- ✅ Event rides (football games, concerts)
- ✅ Campus parking integration
- ✅ Class schedule hints (optional)

**Implementation Time:** 4-5 days
**Competitive Advantage:** HIGH (Unique to campus rideshare)

---

## Feature 1: Campus Buildings Database

**File:** `backend/services/ride-service/app/data/sjsu_locations.py`

```python
"""
SJSU Campus Locations Database
Curated list of common SJSU buildings and landmarks
"""

SJSU_BUILDINGS = [
    {
        "id": "dmh",
        "name": "Duncan Hall",
        "full_name": "Duncan Hall (Engineering)",
        "lat": 37.3327,
        "lng": -121.8816,
        "category": "academic",
        "icon": "school"
    },
    {
        "id": "mlk",
        "name": "MLK Library",
        "full_name": "Dr. Martin Luther King, Jr. Library",
        "lat": 37.3357,
        "lng": -121.8849,
        "category": "library",
        "icon": "library"
    },
    {
        "id": "student_union",
        "name": "Student Union",
        "full_name": "SJSU Student Union",
        "lat": 37.3365,
        "lng": -121.8813,
        "category": "student_services",
        "icon": "restaurant"
    },
    {
        "id": "tower_hall",
        "name": "Tower Hall",
        "full_name": "Tower Hall (Administration)",
        "lat": 37.3352,
        "lng": -121.8813,
        "category": "administration",
        "icon": "office"
    },
    {
        "id": "business",
        "name": "Business Building",
        "full_name": "Lucas Graduate School of Business",
        "lat": 37.3369,
        "lng": -121.8815,
        "category": "academic",
        "icon": "school"
    },
    {
        "id": "sweeney_hall",
        "name": "Sweeney Hall",
        "full_name": "Sweeney Hall",
        "lat": 37.3342,
        "lng": -121.8828,
        "category": "academic",
        "icon": "school"
    },
    {
        "id": "spartan_complex",
        "name": "Spartan Complex",
        "full_name": "Spartan Recreation Center",
        "lat": 37.3333,
        "lng": -121.8798,
        "category": "recreation",
        "icon": "fitness_center"
    },
    {
        "id": "sjsu_stadium",
        "name": "CEFCU Stadium",
        "full_name": "CEFCU Stadium (Football)",
        "lat": 37.3212,
        "lng": -121.8631,
        "category": "sports",
        "icon": "sports_football"
    },
    # Parking lots
    {
        "id": "north_garage",
        "name": "North Parking Garage",
        "full_name": "North Parking Garage",
        "lat": 37.3371,
        "lng": -121.8818,
        "category": "parking",
        "icon": "local_parking"
    },
    {
        "id": "south_garage",
        "name": "South Parking Garage",
        "full_name": "South Parking Garage",
        "lat": 37.3325,
        "lng": -121.8815,
        "category": "parking",
        "icon": "local_parking"
    },
    {
        "id": "west_garage",
        "name": "West Parking Garage",
        "full_name": "West Parking Garage (10th Street)",
        "lat": 37.3338,
        "lng": -121.8838,
        "category": "parking",
        "icon": "local_parking"
    },
    # Popular off-campus locations
    {
        "id": "diridon_station",
        "name": "Diridon Station",
        "full_name": "San Jose Diridon Station (Caltrain/VTA)",
        "lat": 37.3297,
        "lng": -121.9026,
        "category": "transit",
        "icon": "train"
    },
]


# Categorized for easy filtering
CATEGORIES = {
    "academic": "Academic Buildings",
    "library": "Libraries",
    "student_services": "Student Services",
    "administration": "Administration",
    "recreation": "Recreation & Sports",
    "sports": "Sports Venues",
    "parking": "Parking",
    "transit": "Transit Hubs",
    "dining": "Dining",
}


def get_sjsu_locations(category: str = None) -> list:
    """
    Get SJSU campus locations, optionally filtered by category.

    Args:
        category: Filter by category (academic, parking, etc.)

    Returns:
        List of location dicts
    """
    if category:
        return [loc for loc in SJSU_BUILDINGS if loc["category"] == category]
    return SJSU_BUILDINGS


def search_sjsu_locations(query: str) -> list:
    """
    Search SJSU locations by name.

    Args:
        query: Search query (e.g., "library", "parking", "duncan")

    Returns:
        Matching locations
    """
    query_lower = query.lower()
    return [
        loc for loc in SJSU_BUILDINGS
        if query_lower in loc["name"].lower()
        or query_lower in loc["full_name"].lower()
    ]
```

## API Endpoints

**File:** `backend/services/ride-service/app/api/routes/sjsu.py`

```python
"""
SJSU-Specific Endpoints
Campus buildings, events, quick location selection
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from app.data.sjsu_locations import (
    get_sjsu_locations,
    search_sjsu_locations,
    CATEGORIES
)

router = APIRouter()


@router.get("/campus-locations")
async def get_campus_locations(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get SJSU campus locations for quick selection.

    Categories: academic, library, student_services, parking, transit, etc.

    Example Response:
    ```json
    [
        {
            "id": "mlk",
            "name": "MLK Library",
            "full_name": "Dr. Martin Luther King, Jr. Library",
            "lat": 37.3357,
            "lng": -121.8849,
            "category": "library",
            "icon": "library"
        }
    ]
    ```
    """
    return {
        "locations": get_sjsu_locations(category),
        "categories": CATEGORIES
    }


@router.get("/campus-locations/search")
async def search_campus_locations(
    q: str = Query(..., min_length=2, description="Search query")
):
    """
    Search campus locations by name.

    Example: ?q=library
    """
    return {"results": search_sjsu_locations(q)}


@router.get("/campus-locations/{location_id}")
async def get_campus_location_details(location_id: str):
    """Get details for a specific campus location"""
    from app.data.sjsu_locations import SJSU_BUILDINGS

    location = next(
        (loc for loc in SJSU_BUILDINGS if loc["id"] == location_id),
        None
    )

    if not location:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Location not found")

    return location
```

**Add to main.py:**

```python
from app.api.routes import sjsu

app.include_router(
    sjsu.router,
    prefix=f"{settings.API_V1_PREFIX}/sjsu",
    tags=["SJSU Campus"]
)
```

---

## Feature 2: Event Rides

Create special rides for campus events (football games, concerts, etc.)

**File:** `backend/services/ride-service/app/models/event.py`

```python
"""
Campus Events - Special rides for events
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CampusEvent(Base):
    """
    Campus events that users can create rides for.
    Examples: Football games, concerts, career fairs
    """
    __tablename__ = "campus_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)

    # Event details
    event_date = Column(DateTime(timezone=True), nullable=False)
    venue = Column(String(200), nullable=False)
    venue_lat = Column(Float, nullable=False)
    venue_lng = Column(Float, nullable=False)

    # Event type
    category = Column(
        String(50),
        nullable=False
    )  # "football", "basketball", "concert", "career_fair", "club_event"

    # Metadata
    is_featured = Column(Boolean, default=False)
    expected_attendance = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**API:**

```python
@router.get("/events/upcoming")
async def get_upcoming_events(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming campus events"""
    from datetime import datetime, timezone

    result = await db.execute(
        select(CampusEvent)
        .where(CampusEvent.event_date > datetime.now(timezone.utc))
        .order_by(CampusEvent.event_date)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/events/{event_id}/rides")
async def get_event_rides(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get rides going to a specific event"""
    event = await db.get(CampusEvent, event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Find rides with destination near event venue
    from app.utils.geo import haversine_distance

    result = await db.execute(
        select(Ride).where(
            Ride.status == RideStatus.ACTIVE,
            func.date(Ride.departure_time) == event.event_date.date()
        )
    )

    rides = result.scalars().all()

    # Filter by proximity to venue
    event_rides = [
        ride for ride in rides
        if haversine_distance(
            ride.destination_lat,
            ride.destination_lng,
            event.venue_lat,
            event.venue_lng
        ) < 0.5  # Within 500m
    ]

    return event_rides
```

---

## Feature 3: SJSU Email Badge

Update user profile response to show SJSU verification badge:

```python
class UserPublicProfile(BaseModel):
    """Public profile shown to other users"""
    id: UUID
    full_name: str
    profile_photo_url: Optional[str]

    # Ratings
    average_rating_as_driver: float
    average_rating_as_passenger: float
    total_rides_as_driver: int
    total_rides_as_passenger: int

    # Verification badges
    badges: List[str]  # ["sjsu_verified", "top_rated_driver", "100_rides"]

    # Driver info (if applicable)
    car_model: Optional[str]
    car_color: Optional[str]

    @classmethod
    def from_user(cls, user: User):
        badges = []

        if user.sjsu_email_verified:
            badges.append("sjsu_verified")

        if user.phone_verified:
            badges.append("phone_verified")

        if user.email_verified:
            badges.append("email_verified")

        if user.is_top_rated_driver:
            badges.append("top_rated_driver")

        if user.total_completed_rides_as_driver >= 100:
            badges.append("100_rides")

        return cls(
            id=user.id,
            full_name=user.full_name or "Anonymous",
            profile_photo_url=user.profile_photo_url,
            average_rating_as_driver=user.average_rating_as_driver,
            average_rating_as_passenger=user.average_rating_as_passenger,
            total_rides_as_driver=user.total_completed_rides_as_driver,
            total_rides_as_passenger=user.total_completed_rides_as_passenger,
            badges=badges,
            car_model=user.car_model,
            car_color=user.car_color
        )
```

---

<a name="testing"></a>
# PART 2: TESTING & QUALITY ASSURANCE

## Integration Tests

**File:** `backend/tests/integration/test_complete_flow.py`

```python
"""
Integration test for complete user flow:
1. User registration
2. Email verification
3. Create ride
4. Book ride
5. Payment
6. Rate ride
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_rideshare_flow(test_client: AsyncClient):
    """Test end-to-end rideshare flow"""

    # 1. Driver Registration
    driver_response = await test_client.post("/api/v1/auth/register", json={
        "email": "driver@sjsu.edu",
        "password": "SecurePass123",
        "full_name": "John Driver"
    })
    assert driver_response.status_code == 201
    driver_data = driver_response.json()

    # 2. Passenger Registration
    passenger_response = await test_client.post("/api/v1/auth/register", json={
        "email": "passenger@sjsu.edu",
        "password": "SecurePass123",
        "full_name": "Jane Passenger"
    })
    assert passenger_response.status_code == 201

    # 3. Driver creates ride
    driver_token = driver_data["access_token"]

    ride_response = await test_client.post(
        "/api/v1/rides",
        headers={"Authorization": f"Bearer {driver_token}"},
        json={
            "origin": {
                "address": "North Parking Garage, SJSU",
                "lat": 37.3371,
                "lng": -121.8818
            },
            "destination": {
                "address": "South Parking Garage, SJSU",
                "lat": 37.3325,
                "lng": -121.8815
            },
            "departure_time": "2026-01-15T08:00:00Z",
            "available_seats": 3,
            "price_per_seat": 5.00,
            "vehicle": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "license_plate": "ABC123",
                "color": "Blue"
            }
        }
    )
    assert ride_response.status_code == 201
    ride = ride_response.json()

    # 4. Passenger searches for rides
    search_response = await test_client.get("/api/v1/rides/search", params={
        "origin_lat": 37.3371,
        "origin_lng": -121.8818,
        "destination_lat": 37.3325,
        "destination_lng": -121.8815
    })
    assert search_response.status_code == 200
    assert len(search_response.json()) > 0

    # 5. Passenger books ride
    # (Continue with booking, payment, completion, rating flow)
    # ...


@pytest.mark.asyncio
async def test_sjsu_email_verification():
    """Test SJSU email verification flow"""
    # ...


@pytest.mark.asyncio
async def test_rating_system():
    """Test bidirectional rating"""
    # ...
```

## Load Testing

**File:** `backend/tests/load/locustfile.py`

```python
"""
Load testing with Locust
Run: locust -f locustfile.py --host=http://localhost:8002
"""
from locust import HttpUser, task, between


class RideShareUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login on start"""
        response = self.client.post("/api/v1/auth/login/access-token", data={
            "username": "test@sjsu.edu",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3)
    def search_rides(self):
        """Simulate ride search (most common operation)"""
        self.client.get("/api/v1/rides/search", params={
            "origin_lat": 37.3357,
            "origin_lng": -121.8849,
            "destination_lat": 37.3325,
            "destination_lng": -121.8815
        })

    @task(1)
    def create_ride(self):
        """Simulate ride creation"""
        self.client.post(
            "/api/v1/rides",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                # Ride data...
            }
        )

    @task(2)
    def get_profile(self):
        """Get user profile"""
        self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

---

<a name="deployment"></a>
# PART 3: DEPLOYMENT & PRODUCTION SETUP

## Environment Configuration

**File:** `backend/.env.production.example`

```bash
# Service Configuration
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database (Use managed PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@postgres.railway.app:5432/rideshare

# Redis (Use managed Redis)
REDIS_URL=redis://redis.railway.app:6379/0

# Security
SECRET_KEY=<GENERATE_WITH_openssl_rand_hex_32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Stripe (Production keys)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CONNECT_CLIENT_ID=ca_...

# SendGrid (Production)
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=noreply@sjsurideshare.com

# Twilio (Production)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Google Maps
GOOGLE_MAPS_API_KEY=AIza...

# Firebase (Push Notifications)
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# Frontend URL
FRONTEND_URL=https://sjsurideshare.com

# CORS Origins
ALLOWED_ORIGINS=https://sjsurideshare.com,https://app.sjsurideshare.com
```

## Railway Deployment

**File:** `railway.toml`

```toml
[build]
builder = "dockerfile"
dockerfilePath = "services/user-service/Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 10
```

## Docker Compose Production

**File:** `backend/docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  user-service:
    image: sjsu-rideshare-user-service:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - DEBUG=False
    env_file:
      - .env.production
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # Other services...
```

## Health Check Monitoring

**File:** `backend/scripts/healthcheck.sh`

```bash
#!/bin/bash
# Health check script for all services

SERVICES=(
    "http://localhost:8001/health"  # user-service
    "http://localhost:8002/health"  # ride-service
    "http://localhost:8003/health"  # booking-service
    "http://localhost:8004/health"  # notification-service
    "http://localhost:8005/health"  # tracking-service
)

for url in "${SERVICES[@]}"; do
    echo "Checking $url..."
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)

    if [ "$response" != "200" ]; then
        echo "❌ Service unhealthy: $url (HTTP $response)"
        exit 1
    else
        echo "✅ Service healthy: $url"
    fi
done

echo "✅ All services healthy!"
```

---

<a name="launch"></a>
# PART 4: BETA LAUNCH PREPARATION

## Pre-Launch Checklist

```markdown
# SJSU RideShare Beta Launch Checklist

## Backend (Sections 1-13)
- [ ] All services running and healthy
- [ ] Database migrations applied
- [ ] Redis connected
- [ ] Stripe in test mode (switch to live for production)
- [ ] SendGrid configured
- [ ] Firebase push notifications working
- [ ] Google Maps API enabled
- [ ] Rate limiting configured
- [ ] CORS properly set

## Features Implemented
- [ ] User registration & authentication
- [ ] Phone/email verification
- [ ] SJSU email verification
- [ ] Ride creation & search
- [ ] Smart matching algorithm
- [ ] Booking & seat reservation
- [ ] Payment processing (Stripe)
- [ ] Driver payouts (Stripe Connect)
- [ ] Real-time tracking (WebSocket)
- [ ] Notifications (Email + Push)
- [ ] Rating & review system
- [ ] Profile management
- [ ] Saved locations
- [ ] Ride history & receipts
- [ ] Driver dashboard
- [ ] SJSU campus locations
- [ ] Event rides

## Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] End-to-end flow tested
- [ ] Load testing completed
- [ ] Security audit done
- [ ] Payment flow tested (test mode)

## Deployment
- [ ] Production environment configured
- [ ] Environment variables set
- [ ] SSL certificates installed
- [ ] Domain configured (sjsurideshare.com)
- [ ] CDN configured (if needed)
- [ ] Database backups enabled
- [ ] Logging configured
- [ ] Monitoring dashboard set up

## Legal & Compliance
- [ ] Terms of Service written
- [ ] Privacy Policy written
- [ ] GDPR compliance verified
- [ ] Liability insurance purchased (for drivers)
- [ ] University approval obtained (if required)

## Marketing & Onboarding
- [ ] Landing page live
- [ ] Beta signup form
- [ ] Onboarding tutorial ready
- [ ] FAQ page created
- [ ] Support email configured
- [ ] Social media accounts created

## Mobile App (if ready)
- [ ] iOS app submitted to App Store
- [ ] Android app submitted to Google Play
- [ ] Deep linking configured
- [ ] Push notifications working
- [ ] Maps integration working
```

## Beta User Onboarding

**First 100 users strategy:**

1. **Week 1: Friends & Family (20 users)**
   - Personal invitations
   - Test all flows
   - Gather feedback

2. **Week 2: SJSU Student Orgs (50 users)**
   - Reach out to clubs
   - Offer early access
   - Collect testimonials

3. **Week 3: Campus-Wide Soft Launch (100-200 users)**
   - Flyers around campus
   - Social media posts
   - Word of mouth

4. **Week 4+: Public Launch (500+ users)**
   - PR outreach
   - Campus newspaper
   - Instagram/TikTok marketing

---

<a name="monitoring"></a>
# PART 5: POST-LAUNCH MONITORING

## Key Metrics to Track

```python
# backend/scripts/metrics_dashboard.py

"""
Metrics dashboard - Track key business metrics
"""

async def get_platform_metrics():
    """Get key platform metrics"""

    return {
        "users": {
            "total": await count_total_users(),
            "active_this_week": await count_active_users(days=7),
            "drivers": await count_drivers(),
            "verified_sjsu": await count_sjsu_verified(),
        },
        "rides": {
            "total_created": await count_total_rides(),
            "completed_this_week": await count_completed_rides(days=7),
            "average_per_day": await avg_rides_per_day(),
        },
        "bookings": {
            "total": await count_total_bookings(),
            "completion_rate": await calculate_completion_rate(),
            "average_rating": await get_average_rating(),
        },
        "revenue": {
            "total_gmv": await calculate_total_gmv(),  # Gross Merchandise Value
            "platform_fees": await calculate_platform_fees(),
            "this_week": await calculate_revenue(days=7),
        },
        "engagement": {
            "avg_rides_per_user": await avg_rides_per_user(),
            "repeat_user_rate": await calculate_repeat_rate(),
        }
    }
```

## Error Tracking (Sentry)

```python
# backend/shared/utils/sentry_client.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


def initialize_sentry(dsn: str):
    """Initialize Sentry for error tracking"""
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=1.0,
        environment="production"
    )
```

---

# COMPLETE PROMPT FOR CLAUDE CODE

```
PROJECT: SJSU RideShare - Section 13: SJSU Features & Launch Prep

IMPLEMENT:

1. SJSU CAMPUS LOCATIONS:
   - Create sjsu_locations.py with campus buildings
   - API endpoints for campus locations
   - Search functionality
   - Categories (academic, parking, etc.)

2. EVENT RIDES:
   - CampusEvent model
   - Event rides API
   - Filter rides by event

3. SJSU EMAIL BADGE:
   - Show "sjsu_verified" badge in profiles
   - Require @sjsu.edu verification for badge

4. TESTING:
   - Integration tests for complete flow
   - Load testing with Locust
   - Health check scripts

5. DEPLOYMENT:
   - Production environment config
   - Railway deployment
   - Docker production compose
   - Monitoring setup

6. LAUNCH PREP:
   - Pre-launch checklist
   - Metrics dashboard
   - Error tracking (Sentry)

PRIORITY:
1. SJSU campus locations (2 days)
2. Testing suite (2 days)
3. Deployment setup (2 days)
4. Event rides (1 day)
5. Monitoring (1 day)

These are the final features before beta launch!
```

---

# FINAL COMPLETION CHECKLIST

## Backend Complete (Sections 1-13)
- [ ] All 5 microservices running
- [ ] All database tables created
- [ ] All API endpoints tested
- [ ] SJSU-specific features working
- [ ] Tests passing
- [ ] Production deployment ready

## Ready for Beta Launch
- [ ] First 20 users onboarded
- [ ] No critical bugs
- [ ] Monitoring configured
- [ ] Support system ready
- [ ] Marketing materials prepared

---

# CONGRATULATIONS! 🎉

You've built a **production-grade rideshare platform** with:

✅ **11 Database Models**
✅ **50+ API Endpoints**
✅ **5 Microservices**
✅ **Real-time Tracking**
✅ **Payment Processing**
✅ **Rating System**
✅ **SJSU-Specific Features**

**You're ready to launch your beta at SJSU!**

---

# NEXT STEPS

1. **Week 1-2:** Final testing and bug fixes
2. **Week 3:** Soft launch with 20 friends
3. **Week 4:** Expand to 100 beta users
4. **Week 5+:** Public launch at SJSU

**Good luck with your launch! 🚀**
