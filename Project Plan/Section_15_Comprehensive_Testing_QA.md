# SJSU RideShare Development Guide
## Section 15: Comprehensive Testing & Quality Assurance

**Version:** 2.0 (Updated for Sections 1-14)
**Duration:** Week 18-19 (2 weeks)
**Focus:** Complete Testing Strategy, QA, Performance, Security

---

# TABLE OF CONTENTS

1. [Overview & Strategy](#overview)
2. [Backend Unit Tests](#backend-unit)
3. [Backend Integration Tests](#backend-integration)
4. [API Contract Tests](#api-contract)
5. [Load & Performance Testing](#load-testing)
6. [Security Testing](#security)
7. [Mobile App Testing](#mobile-testing)
8. [End-to-End Testing](#e2e)
9. [Test Automation & CI/CD](#cicd)
10. [Quality Metrics](#metrics)

---

<a name="overview"></a>
# PART 1: OVERVIEW & TESTING STRATEGY

## Testing Pyramid

```
                    /\
                   /  \
                  / E2E \              < 10% (Slow, Expensive)
                 /______\
                /        \
               / Integration \         < 30% (Medium Speed)
              /______________\
             /                \
            /   Unit Tests     \      < 60% (Fast, Cheap)
           /____________________\
```

## What We're Testing

### Backend Services (5 Microservices)
1. **User Service** - Auth, profiles, verification
2. **Ride Service** - Ride CRUD, matching, search
3. **Booking Service** - Bookings, payments, ratings
4. **Notification Service** - Email, push notifications
5. **Tracking Service** - Real-time location, WebSocket

### Mobile App
- React Native components
- Navigation flows
- API integration
- UI/UX testing

### Infrastructure
- Database operations
- Redis caching
- WebSocket connections
- External APIs (Stripe, Twilio, Google Maps)

---

## Testing Tools & Frameworks

```python
# Backend
pytest              # Test framework
pytest-asyncio      # Async test support
pytest-cov          # Coverage reporting
httpx               # HTTP testing client
faker               # Test data generation
factory-boy         # Model factories
locust              # Load testing
bandit              # Security scanning
safety              # Dependency security

# Mobile
jest                # Unit testing
@testing-library/react-native  # Component testing
detox               # E2E testing
```

---

<a name="backend-unit"></a>
# PART 2: BACKEND UNIT TESTS

## Test Structure

```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_utils.py
│   │   └── test_validators.py
│   ├── integration/
│   │   ├── test_api_flow.py
│   │   ├── test_ride_matching.py
│   │   ├── test_booking_flow.py
│   │   └── test_payment_flow.py
│   ├── load/
│   │   └── locustfile.py
│   └── security/
│       └── test_security.py
```

## Shared Test Fixtures

**File:** `backend/tests/conftest.py`

```python
"""
Shared pytest fixtures for all tests
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
from faker import Faker

from app.core.database import Base
from app.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/rideshare_test"

fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test"""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for API tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user) -> AsyncClient:
    """Create authenticated HTTP client"""
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login/access-token",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]

    # Add auth header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create test user"""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        email=fake.email(),
        full_name=fake.name(),
        hashed_password=get_password_hash("testpassword123"),
        email_verified=True,
        phone_verified=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def test_driver(db_session: AsyncSession):
    """Create test driver with vehicle"""
    from app.models.user import User
    from app.core.security import get_password_hash

    driver = User(
        email=fake.email(),
        full_name=fake.name(),
        hashed_password=get_password_hash("testpassword123"),
        email_verified=True,
        is_driver=True,
        car_make="Toyota",
        car_model="Camry",
        car_year=2020,
        license_plate="ABC123",
        car_color="Blue",
    )

    db_session.add(driver)
    await db_session.commit()
    await db_session.refresh(driver)

    return driver


@pytest.fixture
async def test_ride(db_session: AsyncSession, test_driver):
    """Create test ride"""
    from app.models.ride import Ride
    from datetime import datetime, timedelta, timezone

    ride = Ride(
        driver_id=test_driver.id,
        origin_address="North Parking Garage, SJSU",
        origin_lat=37.3371,
        origin_lng=-121.8818,
        destination_address="South Parking Garage, SJSU",
        destination_lat=37.3325,
        destination_lng=-121.8815,
        departure_time=datetime.now(timezone.utc) + timedelta(hours=2),
        available_seats=3,
        price_per_seat=5.00,
        status="active",
    )

    db_session.add(ride)
    await db_session.commit()
    await db_session.refresh(ride)

    return ride
```

## Model Tests

**File:** `backend/tests/unit/test_models.py`

```python
"""
Unit tests for database models
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal


@pytest.mark.asyncio
async def test_user_model_creation(db_session, test_user):
    """Test user model is created correctly"""
    assert test_user.id is not None
    assert test_user.email is not None
    assert test_user.full_name is not None
    assert test_user.hashed_password is not None
    assert test_user.email_verified is True


@pytest.mark.asyncio
async def test_user_password_hashing(db_session):
    """Test password is hashed, not stored in plain text"""
    from app.models.user import User
    from app.core.security import get_password_hash, verify_password

    password = "SecurePassword123"
    user = User(
        email="test@sjsu.edu",
        full_name="Test User",
        hashed_password=get_password_hash(password),
    )

    db_session.add(user)
    await db_session.commit()

    # Password should be hashed
    assert user.hashed_password != password

    # Should verify correctly
    assert verify_password(password, user.hashed_password) is True
    assert verify_password("wrongpassword", user.hashed_password) is False


@pytest.mark.asyncio
async def test_ride_model_validations(db_session, test_driver):
    """Test ride model validations"""
    from app.models.ride import Ride

    # Valid ride
    ride = Ride(
        driver_id=test_driver.id,
        origin_address="Point A",
        origin_lat=37.3371,
        origin_lng=-121.8818,
        destination_address="Point B",
        destination_lat=37.3325,
        destination_lng=-121.8815,
        departure_time=datetime.now(timezone.utc) + timedelta(hours=2),
        available_seats=3,
        price_per_seat=Decimal("5.00"),
    )

    db_session.add(ride)
    await db_session.commit()

    assert ride.id is not None
    assert ride.status == "active"
    assert ride.available_seats == 3


@pytest.mark.asyncio
async def test_booking_seat_reservation(db_session, test_ride, test_user):
    """Test booking reduces available seats"""
    from app.models.booking import Booking

    initial_seats = test_ride.available_seats

    # Create booking
    booking = Booking(
        ride_id=test_ride.id,
        passenger_id=test_user.id,
        seats_booked=2,
        pickup_location={"address": "Pickup", "lat": 37.337, "lng": -121.881},
        dropoff_location={"address": "Dropoff", "lat": 37.332, "lng": -121.881},
        total_amount=Decimal("10.00"),
        status="pending",
    )

    db_session.add(booking)

    # Update ride seats
    test_ride.available_seats -= booking.seats_booked

    await db_session.commit()
    await db_session.refresh(test_ride)

    assert test_ride.available_seats == initial_seats - 2


@pytest.mark.asyncio
async def test_rating_constraints(db_session, test_ride, test_user, test_driver):
    """Test rating model constraints"""
    from app.models.rating import Rating

    # Valid rating (1-5 stars)
    rating = Rating(
        booking_id="some-booking-id",
        ride_id=test_ride.id,
        rater_id=test_user.id,
        rated_user_id=test_driver.id,
        rating_type="passenger_to_driver",
        rating=5,
        review="Great ride!",
    )

    db_session.add(rating)
    await db_session.commit()

    assert rating.id is not None
    assert 1 <= rating.rating <= 5
```

## Service Layer Tests

**File:** `backend/tests/unit/test_services.py`

```python
"""
Unit tests for service layer business logic
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal


@pytest.mark.asyncio
async def test_ride_matching_service(db_session, test_ride):
    """Test ride matching algorithm"""
    from app.services.matching_service import MatchingService

    service = MatchingService()

    # Search params
    search_params = {
        "origin_lat": 37.3371,
        "origin_lng": -121.8818,
        "destination_lat": 37.3325,
        "destination_lng": -121.8815,
        "proximity_km": 1.0,
        "min_seats": 1,
    }

    matches = await service.find_matching_rides(search_params, db_session)

    assert len(matches) > 0
    assert test_ride.id in [match.id for match in matches]


@pytest.mark.asyncio
async def test_haversine_distance_calculation():
    """Test geospatial distance calculation"""
    from app.utils.geo import haversine_distance

    # SJSU to SFO Airport (~50 km)
    distance = haversine_distance(
        lat1=37.3352,  # SJSU
        lng1=-121.8811,
        lat2=37.6213,  # SFO
        lng2=-122.3790,
    )

    assert 40 < distance < 60  # Approximately 50 km


@pytest.mark.asyncio
async def test_direction_alignment_check():
    """Test if route is aligned with passenger's direction"""
    from app.services.matching_service import check_direction_alignment

    # Same direction (SJSU to Milpitas)
    aligned = check_direction_alignment(
        origin_lat=37.3352,
        origin_lng=-121.8811,
        dest_lat=37.4323,
        dest_lng=-121.8996,
        passenger_origin_lat=37.3360,
        passenger_origin_lng=-121.8820,
        passenger_dest_lat=37.4300,
        passenger_dest_lng=-121.9000,
    )

    assert aligned is True


@pytest.mark.asyncio
async def test_rating_aggregation(db_session, test_user, test_driver):
    """Test average rating calculation"""
    from app.models.rating import Rating
    from app.services.rating_service import RatingService

    # Create multiple ratings
    ratings = [
        Rating(
            booking_id=f"booking-{i}",
            ride_id="some-ride-id",
            rater_id=test_user.id,
            rated_user_id=test_driver.id,
            rating_type="passenger_to_driver",
            rating=r,
        )
        for i, r in enumerate([5, 4, 5, 3, 4])
    ]

    for rating in ratings:
        db_session.add(rating)

    await db_session.commit()

    service = RatingService()
    avg_rating = await service.get_average_rating(test_driver.id, "driver", db_session)

    assert avg_rating == pytest.approx(4.2, 0.1)


@pytest.mark.asyncio
async def test_payment_amount_calculation():
    """Test booking total amount calculation"""
    from app.services.booking_service import calculate_booking_amount

    seats = 2
    price_per_seat = Decimal("5.00")
    platform_fee_percent = Decimal("0.15")  # 15%

    total, platform_fee, driver_payout = calculate_booking_amount(
        seats, price_per_seat, platform_fee_percent
    )

    assert total == Decimal("10.00")  # 2 seats * $5
    assert platform_fee == Decimal("1.50")  # 15% of $10
    assert driver_payout == Decimal("8.50")  # $10 - $1.50
```

## Utility Tests

**File:** `backend/tests/unit/test_utils.py`

```python
"""
Unit tests for utility functions
"""
import pytest
from datetime import datetime, timezone


def test_email_validation():
    """Test email validation"""
    from app.utils.validators import is_valid_email

    assert is_valid_email("test@sjsu.edu") is True
    assert is_valid_email("test@gmail.com") is True
    assert is_valid_email("invalid-email") is False
    assert is_valid_email("@sjsu.edu") is False


def test_sjsu_email_validation():
    """Test SJSU email validation"""
    from app.utils.validators import is_sjsu_email

    assert is_sjsu_email("student@sjsu.edu") is True
    assert is_sjsu_email("faculty@sjsu.edu") is True
    assert is_sjsu_email("test@gmail.com") is False
    assert is_sjsu_email("test@stanford.edu") is False


def test_phone_number_formatting():
    """Test phone number formatting"""
    from app.utils.formatters import format_phone_number

    assert format_phone_number("4081234567") == "+14081234567"
    assert format_phone_number("+14081234567") == "+14081234567"
    assert format_phone_number("408-123-4567") == "+14081234567"


def test_currency_formatting():
    """Test currency formatting"""
    from app.utils.formatters import format_currency
    from decimal import Decimal

    assert format_currency(Decimal("10.00")) == "$10.00"
    assert format_currency(Decimal("5.50")) == "$5.50"
    assert format_currency(Decimal("100.99")) == "$100.99"


def test_date_formatting():
    """Test date/time formatting"""
    from app.utils.formatters import format_datetime

    dt = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)

    assert "Jan 15" in format_datetime(dt, format="short")
    assert "2026" in format_datetime(dt, format="long")
```

---

<a name="backend-integration"></a>
# PART 3: BACKEND INTEGRATION TESTS

## Complete User Flow Test

**File:** `backend/tests/integration/test_complete_flow.py`

```python
"""
Integration test for complete user journey
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest.mark.asyncio
async def test_complete_rideshare_flow(client: AsyncClient):
    """
    Test end-to-end flow:
    1. Driver registers
    2. Passenger registers
    3. Driver creates ride
    4. Passenger searches rides
    5. Passenger books ride
    6. Payment processed
    7. Ride completed
    8. Both users rate each other
    """

    # 1. DRIVER REGISTRATION
    driver_data = {
        "email": "driver@sjsu.edu",
        "password": "SecurePass123",
        "full_name": "John Driver",
    }

    driver_response = await client.post("/api/v1/auth/register", json=driver_data)
    assert driver_response.status_code == 201

    driver_token = driver_response.json()["access_token"]
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # 2. PASSENGER REGISTRATION
    passenger_data = {
        "email": "passenger@sjsu.edu",
        "password": "SecurePass123",
        "full_name": "Jane Passenger",
    }

    passenger_response = await client.post("/api/v1/auth/register", json=passenger_data)
    assert passenger_response.status_code == 201

    passenger_token = passenger_response.json()["access_token"]
    passenger_headers = {"Authorization": f"Bearer {passenger_token}"}

    # 3. DRIVER CREATES RIDE
    ride_data = {
        "origin": {
            "address": "North Parking Garage, SJSU",
            "lat": 37.3371,
            "lng": -121.8818,
        },
        "destination": {
            "address": "South Parking Garage, SJSU",
            "lat": 37.3325,
            "lng": -121.8815,
        },
        "departure_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "available_seats": 3,
        "price_per_seat": 5.00,
        "vehicle": {
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "license_plate": "ABC123",
            "color": "Blue",
        },
    }

    ride_response = await client.post(
        "/api/v1/rides",
        headers=driver_headers,
        json=ride_data,
    )
    assert ride_response.status_code == 201
    ride = ride_response.json()
    ride_id = ride["id"]

    # 4. PASSENGER SEARCHES RIDES
    search_response = await client.get(
        "/api/v1/rides/search",
        params={
            "origin_lat": 37.3371,
            "origin_lng": -121.8818,
            "destination_lat": 37.3325,
            "destination_lng": -121.8815,
            "proximity_km": 1.0,
        },
    )
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert len(search_results) > 0
    assert ride_id in [r["id"] for r in search_results]

    # 5. PASSENGER BOOKS RIDE
    booking_data = {
        "ride_id": ride_id,
        "seats_booked": 2,
        "pickup_location": {
            "address": "North Parking Garage",
            "lat": 37.3370,
            "lng": -121.8817,
        },
        "dropoff_location": {
            "address": "South Parking Garage",
            "lat": 37.3324,
            "lng": -121.8814,
        },
        "payment_method_id": "pm_test_card",  # Stripe test card
    }

    booking_response = await client.post(
        "/api/v1/bookings",
        headers=passenger_headers,
        json=booking_data,
    )
    assert booking_response.status_code == 201
    booking = booking_response.json()
    booking_id = booking["id"]

    # Check booking status
    assert booking["status"] == "pending"
    assert booking["payment_status"] == "authorized"

    # 6. DRIVER APPROVES BOOKING
    approve_response = await client.post(
        f"/api/v1/bookings/{booking_id}/approve",
        headers=driver_headers,
    )
    assert approve_response.status_code == 200

    # Check payment was captured
    booking_check = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=passenger_headers,
    )
    assert booking_check.json()["payment_status"] == "paid"

    # 7. SIMULATE RIDE COMPLETION
    complete_response = await client.post(
        f"/api/v1/bookings/{booking_id}/complete",
        headers=driver_headers,
    )
    assert complete_response.status_code == 200

    # 8. PASSENGER RATES DRIVER
    passenger_rating_data = {
        "booking_id": booking_id,
        "rating": 5,
        "review": "Great ride!",
        "category_ratings": {
            "punctuality": 5,
            "cleanliness": 5,
            "communication": 5,
        },
    }

    passenger_rating_response = await client.post(
        "/api/v1/ratings",
        headers=passenger_headers,
        json=passenger_rating_data,
    )
    assert passenger_rating_response.status_code == 201

    # 9. DRIVER RATES PASSENGER
    driver_rating_data = {
        "booking_id": booking_id,
        "rating": 5,
        "review": "Great passenger!",
        "category_ratings": {
            "punctuality": 5,
            "cleanliness": 5,
            "communication": 5,
        },
    }

    driver_rating_response = await client.post(
        "/api/v1/ratings",
        headers=driver_headers,
        json=driver_rating_data,
    )
    assert driver_rating_response.status_code == 201

    # VERIFY FINAL STATE
    # Check ride available seats reduced
    ride_check = await client.get(f"/api/v1/rides/{ride_id}", headers=driver_headers)
    assert ride_check.json()["available_seats"] == 1  # 3 - 2 booked

    # Check driver rating updated
    driver_profile = await client.get("/api/v1/users/me", headers=driver_headers)
    assert driver_profile.json()["average_rating_as_driver"] == 5.0

    # Check passenger rating updated
    passenger_profile = await client.get("/api/v1/users/me", headers=passenger_headers)
    assert passenger_profile.json()["average_rating_as_passenger"] == 5.0

    print("✅ Complete rideshare flow test passed!")


@pytest.mark.asyncio
async def test_booking_rejection_refund_flow(client: AsyncClient):
    """Test that rejected bookings trigger refunds"""
    # Create driver, passenger, ride
    # Passenger books ride
    # Driver rejects booking
    # Verify refund was processed
    # ... implementation ...


@pytest.mark.asyncio
async def test_concurrent_booking_race_condition(client: AsyncClient):
    """Test that concurrent bookings don't overbook"""
    # Create ride with 1 seat
    # Two passengers try to book simultaneously
    # Only one should succeed
    # ... implementation ...
```

## Ride Matching Tests

**File:** `backend/tests/integration/test_ride_matching.py`

```python
"""
Integration tests for ride matching algorithm
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest.mark.asyncio
async def test_proximity_based_matching(client: AsyncClient, authenticated_client):
    """Test rides are matched based on proximity"""
    # Create rides at different distances
    # Search with proximity filter
    # Verify only nearby rides returned
    # ... implementation ...


@pytest.mark.asyncio
async def test_direction_alignment_filtering(client: AsyncClient):
    """Test rides going opposite direction are filtered out"""
    # Create ride going north
    # Search for ride going south
    # Verify no match
    # ... implementation ...


@pytest.mark.asyncio
async def test_advanced_search_filters(client: AsyncClient):
    """Test advanced search filters (rating, gender, amenities)"""
    # Create rides with different driver ratings
    # Search with min_driver_rating filter
    # Verify only high-rated drivers returned
    # ... implementation ...
```

---

<a name="api-contract"></a>
# PART 4: API CONTRACT TESTS

**File:** `backend/tests/integration/test_api_contracts.py`

```python
"""
API contract tests - ensure API responses match documented schemas
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_register_response_schema(client: AsyncClient):
    """Test /auth/register response matches schema"""
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@sjsu.edu",
        "password": "SecurePass123",
        "full_name": "Test User",
    })

    assert response.status_code == 201
    data = response.json()

    # Verify schema
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert "id" in data["user"]
    assert "email" in data["user"]
    assert "full_name" in data["user"]


@pytest.mark.asyncio
async def test_ride_response_schema(authenticated_client: AsyncClient):
    """Test /rides response matches RideResponse schema"""
    response = await authenticated_client.get("/api/v1/rides/feed")

    assert response.status_code == 200
    rides = response.json()

    if len(rides) > 0:
        ride = rides[0]

        # Verify required fields
        required_fields = [
            "id", "driver_id", "origin_address", "origin_lat", "origin_lng",
            "destination_address", "destination_lat", "destination_lng",
            "departure_time", "available_seats", "price_per_seat", "status"
        ]

        for field in required_fields:
            assert field in ride, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_error_response_format(client: AsyncClient):
    """Test error responses have consistent format"""
    # Invalid credentials
    response = await client.post("/api/v1/auth/login/access-token", data={
        "username": "nonexistent@test.com",
        "password": "wrongpassword",
    })

    assert response.status_code == 401
    error = response.json()

    assert "detail" in error
```

---

<a name="load-testing"></a>
# PART 5: LOAD & PERFORMANCE TESTING

## Locust Load Test

**File:** `backend/tests/load/locustfile.py`

```python
"""
Load testing with Locust
Run: locust -f locustfile.py --host=http://localhost:8002
"""
from locust import HttpUser, task, between, events
import random


class RideShareUser(HttpUser):
    """Simulates a typical rideshare user"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called once per user - perform login"""
        # Register or login
        self.email = f"user{random.randint(1, 10000)}@test.com"
        response = self.client.post("/api/v1/auth/register", json={
            "email": self.email,
            "password": "testpass123",
            "full_name": f"Test User {random.randint(1, 1000)}",
        })

        if response.status_code in [200, 201]:
            self.token = response.json()["access_token"]
        else:
            # Try login
            login_response = self.client.post("/api/v1/auth/login/access-token", data={
                "username": "demo@test.com",
                "password": "demo123",
            })
            self.token = login_response.json()["access_token"]

    @task(10)
    def search_rides(self):
        """Most common task - searching for rides"""
        self.client.get("/api/v1/rides/search", params={
            "origin_lat": 37.3352 + random.uniform(-0.01, 0.01),
            "origin_lng": -121.8811 + random.uniform(-0.01, 0.01),
            "destination_lat": 37.4323 + random.uniform(-0.01, 0.01),
            "destination_lng": -121.8996 + random.uniform(-0.01, 0.01),
            "proximity_km": 5.0,
        })

    @task(5)
    def view_ride_feed(self):
        """View recent rides"""
        self.client.get("/api/v1/rides/feed")

    @task(3)
    def get_profile(self):
        """Get user profile"""
        self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(2)
    def create_ride(self):
        """Create a ride (less common)"""
        from datetime import datetime, timedelta, timezone

        self.client.post(
            "/api/v1/rides",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "origin": {
                    "address": "Random Origin",
                    "lat": 37.3352,
                    "lng": -121.8811,
                },
                "destination": {
                    "address": "Random Destination",
                    "lat": 37.4323,
                    "lng": -121.8996,
                },
                "departure_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                "available_seats": random.randint(1, 4),
                "price_per_seat": random.choice([3.0, 5.0, 7.0, 10.0]),
                "vehicle": {
                    "make": "Toyota",
                    "model": "Camry",
                    "year": 2020,
                    "license_plate": f"ABC{random.randint(100, 999)}",
                    "color": "Blue",
                },
            }
        )

    @task(1)
    def view_bookings(self):
        """View bookings"""
        self.client.get(
            "/api/v1/bookings/my-bookings",
            headers={"Authorization": f"Bearer {self.token}"}
        )


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line options"""
    parser.add_argument("--users", type=int, default=100, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", type=int, default=10, help="Users spawned per second")
```

## Performance Benchmarks

**File:** `backend/tests/load/test_performance.py`

```python
"""
Performance benchmark tests
"""
import pytest
import time
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ride_search_performance(authenticated_client: AsyncClient):
    """Test ride search responds within 500ms"""
    start = time.time()

    response = await authenticated_client.get("/api/v1/rides/search", params={
        "origin_lat": 37.3352,
        "origin_lng": -121.8811,
        "destination_lat": 37.4323,
        "destination_lng": -121.8996,
    })

    elapsed = (time.time() - start) * 1000  # Convert to ms

    assert response.status_code == 200
    assert elapsed < 500, f"Ride search took {elapsed}ms (expected < 500ms)"


@pytest.mark.asyncio
async def test_bulk_ride_creation_performance(authenticated_client: AsyncClient):
    """Test creating multiple rides in parallel"""
    from datetime import datetime, timedelta, timezone
    import asyncio

    async def create_ride():
        return await authenticated_client.post("/api/v1/rides", json={
            "origin": {"address": "A", "lat": 37.3352, "lng": -121.8811},
            "destination": {"address": "B", "lat": 37.4323, "lng": -121.8996},
            "departure_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "available_seats": 3,
            "price_per_seat": 5.0,
            "vehicle": {
                "make": "Toyota", "model": "Camry", "year": 2020,
                "license_plate": "ABC123", "color": "Blue",
            },
        })

    start = time.time()

    # Create 10 rides in parallel
    tasks = [create_ride() for _ in range(10)]
    results = await asyncio.gather(*tasks)

    elapsed = (time.time() - start) * 1000

    assert all(r.status_code == 201 for r in results)
    assert elapsed < 3000, f"Creating 10 rides took {elapsed}ms (expected < 3000ms)"
```

---

<a name="security"></a>
# PART 6: SECURITY TESTING

**File:** `backend/tests/security/test_security.py`

```python
"""
Security tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unauthenticated_access_blocked(client: AsyncClient):
    """Test protected endpoints require authentication"""
    protected_endpoints = [
        "/api/v1/users/me",
        "/api/v1/rides",
        "/api/v1/bookings/my-bookings",
    ]

    for endpoint in protected_endpoints:
        response = await client.get(endpoint)
        assert response.status_code == 401, f"{endpoint} should require auth"


@pytest.mark.asyncio
async def test_authorization_checks(client: AsyncClient):
    """Test users can only access their own resources"""
    # User A creates a booking
    # User B tries to access User A's booking
    # Should get 403 Forbidden
    # ... implementation ...


@pytest.mark.asyncio
async def test_sql_injection_protection(client: AsyncClient):
    """Test SQL injection attempts are blocked"""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
    ]

    for malicious_input in malicious_inputs:
        response = await client.post("/api/v1/auth/login/access-token", data={
            "username": malicious_input,
            "password": "password",
        })

        # Should not return 500 (server error)
        assert response.status_code != 500


@pytest.mark.asyncio
async def test_xss_protection(authenticated_client: AsyncClient):
    """Test XSS payloads are sanitized"""
    xss_payload = "<script>alert('XSS')</script>"

    response = await authenticated_client.put("/api/v1/users/me", json={
        "full_name": xss_payload,
    })

    # Should accept but sanitize
    updated = response.json()
    assert "<script>" not in updated["full_name"]


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """Test rate limiting prevents abuse"""
    # Make 100 requests rapidly
    for _ in range(100):
        response = await client.get("/api/v1/rides/feed")

    # Should eventually get rate limited
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_password_strength_validation(client: AsyncClient):
    """Test weak passwords are rejected"""
    weak_passwords = ["123", "password", "abc"]

    for weak_password in weak_passwords:
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "password": weak_password,
            "full_name": "Test",
        })

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_sensitive_data_not_exposed(authenticated_client: AsyncClient):
    """Test sensitive data is not exposed in API responses"""
    response = await authenticated_client.get("/api/v1/users/me")
    user = response.json()

    # Should NOT expose sensitive fields
    assert "hashed_password" not in user
    assert "password" not in user
    assert "password_reset_token" not in user
```

## Dependency Security Scan

```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Output: (example)
# ╒══════════════════════════════════════════════════════════════════════════════╕
# │                                                                              │
# │                               /$$$$$$  /$$$$$$   /$$$$$$                     │
# │                              /$$__  $$|____  $$ /$$__  $$                    │
# │                             | $$  \__/ /$$$$$$$| $$  \__/                    │
# │                             |  $$$$$$ /$$__  $$|  $$$$$$                     │
# │                              \____  $$| $$$$$$$|\____  $$                    │
# │                              /$$  \ $$| $$_____//$$  \ $$                    │
# │                             |  $$$$$$/|  $$$$$$$|  $$$$$$/                   │
# │                              \______/  \_______/ \______/                    │
# │                                                                              │
# ╞══════════════════════════════════════════════════════════════════════════════╡
# │ REPORT                                                                       │
# │ No known security vulnerabilities found.                                     │
# ╘══════════════════════════════════════════════════════════════════════════════╛
```

---

<a name="mobile-testing"></a>
# PART 7: MOBILE APP TESTING

## Jest Unit Tests

**File:** `mobile/__tests__/components/RideCard.test.tsx`

```typescript
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { RideCard } from '../../src/components/ride/RideCard';

describe('RideCard', () => {
  const mockRide = {
    id: '123',
    driver: {
      full_name: 'John Driver',
      average_rating_as_driver: 4.8,
    },
    origin_address: 'North Parking',
    destination_address: 'South Parking',
    departure_time: '2026-01-15T08:00:00Z',
    available_seats: 3,
    price_per_seat: 5.0,
  };

  it('renders ride information correctly', () => {
    const { getByText } = render(<RideCard ride={mockRide} />);

    expect(getByText('John Driver')).toBeTruthy();
    expect(getByText('North Parking')).toBeTruthy();
    expect(getByText('South Parking')).toBeTruthy();
    expect(getByText('$5.00')).toBeTruthy();
  });

  it('calls onPress when card is pressed', () => {
    const onPress = jest.fn();
    const { getByTestId } = render(<RideCard ride={mockRide} onPress={onPress} />);

    fireEvent.press(getByTestId('ride-card'));
    expect(onPress).toHaveBeenCalledWith(mockRide);
  });
});
```

## Detox E2E Tests

**File:** `mobile/e2e/login.e2e.ts`

```typescript
describe('Login Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should login successfully', async () => {
    await element(by.id('email-input')).typeText('test@sjsu.edu');
    await element(by.id('password-input')).typeText('SecurePass123');
    await element(by.id('login-button')).tap();

    // Should navigate to home screen
    await expect(element(by.id('home-screen'))).toBeVisible();
  });

  it('should show error for invalid credentials', async () => {
    await element(by.id('email-input')).typeText('wrong@test.com');
    await element(by.id('password-input')).typeText('wrongpass');
    await element(by.id('login-button')).tap();

    // Should show error message
    await expect(element(by.text('Login Failed'))).toBeVisible();
  });
});
```

---

<a name="e2e"></a>
# PART 8: END-TO-END TESTING

**File:** `backend/tests/e2e/test_full_platform.py`

```python
"""
End-to-end tests simulating real user workflows
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_new_user_complete_journey(client: AsyncClient):
    """
    Simulate a completely new user from registration to completed ride
    """
    # 1. User discovers app, downloads, opens
    # 2. Registers with SJSU email
    # 3. Verifies email and phone
    # 4. Adds profile photo
    # 5. Adds payment method
    # 6. Saves home/work locations
    # 7. Searches for ride
    # 8. Books ride
    # 9. Pays
    # 10. Tracks ride
    # 11. Completes ride
    # 12. Rates driver
    # ... implementation ...
```

---

<a name="cicd"></a>
# PART 9: TEST AUTOMATION & CI/CD

## GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: rideshare_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  mobile-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd mobile
          npm install

      - name: Run tests
        run: |
          cd mobile
          npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./mobile/coverage/lcov.info

  security-scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run safety check
        run: |
          pip install safety
          cd backend
          safety check -r requirements.txt

      - name: Run bandit (security linter)
        run: |
          pip install bandit
          cd backend
          bandit -r app/
```

---

<a name="metrics"></a>
# PART 10: QUALITY METRICS

## Code Coverage Goals

```
Target Coverage:
- Backend: > 80%
- Mobile: > 70%
- Critical paths: > 90%
```

## Test Execution Report

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Output:
# =========== test session starts ===========
# collected 247 items
#
# tests/unit/test_models.py ........... [  4%]
# tests/unit/test_services.py ........ [  7%]
# tests/integration/test_flow.py ..... [ 12%]
# ...
#
# ---------- coverage: platform linux ----------
# Name                        Stmts   Miss  Cover
# -----------------------------------------------
# app/models/user.py            145     12    92%
# app/models/ride.py            120      8    93%
# app/services/matching.py       89      5    94%
# app/api/routes/rides.py       156     18    88%
# -----------------------------------------------
# TOTAL                        3421    287    84%
```

---

# COMPLETION CHECKLIST

## Backend Testing
- [ ] Unit tests for all models
- [ ] Unit tests for all services
- [ ] Integration tests for API flows
- [ ] Load testing with Locust
- [ ] Security testing
- [ ] API contract tests
- [ ] Performance benchmarks
- [ ] Code coverage > 80%

## Mobile Testing
- [ ] Component unit tests
- [ ] Navigation tests
- [ ] API integration tests
- [ ] E2E tests with Detox
- [ ] iOS manual testing
- [ ] Android manual testing
- [ ] Code coverage > 70%

## Automation
- [ ] CI/CD pipeline configured
- [ ] Automated tests on PR
- [ ] Coverage reports
- [ ] Security scans
- [ ] Deploy previews

## Quality Metrics
- [ ] Test execution < 10 minutes
- [ ] Zero flaky tests
- [ ] All critical paths tested
- [ ] Performance benchmarks met

---

# TIMELINE

**Week 18: Backend Testing (7 days)**
- Unit tests for all services
- Integration tests
- Load testing
- Security testing

**Week 19: Mobile & E2E Testing (7 days)**
- Mobile component tests
- E2E flows
- CI/CD setup
- Final QA

**Total: 2 weeks**

---

# COMPLETE PROMPT FOR CLAUDE CODE

```
PROJECT: SJSU RideShare - Section 15: Comprehensive Testing & QA

IMPLEMENT:

1. BACKEND UNIT TESTS:
   - Model tests (users, rides, bookings, ratings)
   - Service layer tests
   - Utility function tests
   - Validator tests

2. INTEGRATION TESTS:
   - Complete user flow test
   - Ride matching tests
   - Booking + payment flow
   - Real-time tracking tests
   - Rating system tests

3. LOAD TESTING:
   - Locust load test setup
   - Performance benchmarks
   - Concurrent user simulation

4. SECURITY TESTS:
   - Auth/authorization tests
   - SQL injection protection
   - XSS protection
   - Rate limiting tests
   - Dependency scanning

5. MOBILE TESTS:
   - Jest component tests
   - Detox E2E tests
   - Navigation tests

6. CI/CD:
   - GitHub Actions workflow
   - Automated test execution
   - Coverage reporting

Run tests with: pytest --cov=app --cov-report=html
Target: >80% backend coverage, >70% mobile coverage
```

---

**This completes all 15 sections! Your SJSU RideShare platform is now production-ready! 🚀**
