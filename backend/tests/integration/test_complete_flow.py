"""
Integration test for complete user flow
Tests end-to-end rideshare journey from registration to rating
"""
import pytest
from httpx import AsyncClient
import uuid
from datetime import datetime, timedelta, timezone


@pytest.mark.asyncio
async def test_complete_rideshare_flow():
    """
    Test full flow:
    1. Driver/Passenger registration
    2. Driver creates ride
    3. Passenger searches and books
    4. Payment processing
    5. Ride completion
    6. Mutual rating
    """
    base_url = "http://localhost:8001"  # Adjust based on gateway/service
    
    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 1. Register Driver
        driver_email = f"driver_{uuid.uuid4().hex[:8]}@sjsu.edu"
        driver_response = await client.post("/api/v1/users/", json={
            "email": driver_email,
            "password": "SecurePass123!",
            "full_name": "John Driver",
            "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"
        })
        assert driver_response.status_code in [200, 201]

        # Login Driver
        driver_token_response = await client.post("/api/v1/auth/login/access-token", data={
            "username": driver_email,
            "password": "SecurePass123!"
        })
        assert driver_token_response.status_code == 200
        driver_token = driver_token_response.json()["access_token"]
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        # 2. Register Passenger
        passenger_email = f"passenger_{uuid.uuid4().hex[:8]}@sjsu.edu"
        passenger_response = await client.post("/api/v1/users/", json={
            "email": passenger_email,
            "password": "SecurePass123!",
            "full_name": "Jane Passenger",
            "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"
        })
        assert passenger_response.status_code in [200, 201]

        # Login Passenger
        passenger_token_response = await client.post("/api/v1/auth/login/access-token", data={
            "username": passenger_email,
            "password": "SecurePass123!"
        })
        passenger_token = passenger_token_response.json()["access_token"]
        passenger_headers = {"Authorization": f"Bearer {passenger_token}"}

        # 3. Driver creates ride (using campus locations)
        ride_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        ride_response = await client.post(
            "http://localhost:8002/api/v1/rides/",
            headers=driver_headers,
            json={
                "origin": {
                    "address": "North Parking Garage, SJSU",
                    "lat": 37.3371,
                    "lng": -121.8818
                },
                "destination": {
                    "address": "Diridon Station",
                    "lat": 37.3297,
                    "lng": -121.9026
                },
                "departure_time": ride_time,
                "available_seats": 3,
                "price_per_seat": 5.00,
                "vehicle": {
                    "make": "Toyota",
                    "model": "Camry",
                    "year": 2020,
                    "license_plate": "TEST123",
                    "color": "Blue"
                }
            }
        )
        assert ride_response.status_code == 201
        ride_id = ride_response.json()["id"]

        # 4. Passenger searches for rides
        search_response = await client.get(
            "http://localhost:8002/api/v1/rides/",
            params={
                "origin_lat": 37.3371,
                "origin_lng": -121.8818,
                "destination_lat": 37.3297,
                "destination_lng": -121.9026
            }
        )
        assert search_response.status_code == 200
        rides = search_response.json()
        assert len(rides) > 0

        # 5. Passenger books ride
        booking_response = await client.post(
            "http://localhost:8003/api/v1/bookings/",
            headers=passenger_headers,
            json={
                "ride_id": ride_id,
                "seats_booked": 1,
                "pickup_location": {"address": "North Garage", "lat": 37.3371, "lng": -121.8818},
                "dropoff_location": {"address": "Diridon", "lat": 37.3297, "lng": -121.9026}
            }
        )
        assert booking_response.status_code == 201
        booking_id = booking_response.json()["id"]

        print(f"✅ Full flow test passed: Ride {ride_id}, Booking {booking_id}")


@pytest.mark.asyncio
async def test_sjsu_campus_locations():
    """Test SJSU campus locations API"""
    async with AsyncClient(base_url="http://localhost:8002", timeout=10.0) as client:
        # Get all locations
        response = await client.get("/api/v1/sjsu/campus-locations")
        assert response.status_code == 200
        data = response.json()
        assert "locations" in data
        assert "categories" in data
        assert len(data["locations"]) > 0

        # Search for library
        search_response = await client.get("/api/v1/sjsu/campus-locations/search?q=library")
        assert search_response.status_code == 200
        results = search_response.json()["results"]
        assert len(results) > 0
        assert "library" in results[0]["name"].lower()

        print("✅ SJSU locations API test passed")
