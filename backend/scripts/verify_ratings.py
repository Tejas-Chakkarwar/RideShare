
import asyncio
import httpx
import uuid
import sys
from datetime import datetime, timedelta, timezone

# Configuration
USER_SERVICE_URL = "http://localhost:8001"
RIDE_SERVICE_URL = "http://localhost:8002"
BOOKING_SERVICE_URL = "http://localhost:8003"

async def main():
    print("🚀 Starting Rating Verification Script...")

    async with httpx.AsyncClient() as client:
        # 1. Create/Login Driver
        print("\nSee 1: Setting up Driver...")
        driver_email = f"driver_{uuid.uuid4().hex[:8]}@example.com"
        driver_data = {
            "email": driver_email,
            "password": "password123",
            "full_name": "Test Driver",
            "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"
        }
        
        # Register
        resp = await client.post(f"{USER_SERVICE_URL}/api/v1/users/", json=driver_data)
        if resp.status_code not in [200, 201]:
            print(f"Driver registration failed: {resp.text}")
            # Login if exists
            pass
        
        # Login
        resp = await client.post(f"{USER_SERVICE_URL}/api/v1/auth/login/access-token", data={
            "username": driver_email,
            "password": "password123"
        })
        if resp.status_code != 200:
             print(f"Driver login failed: {resp.text}")
             sys.exit(1)

        driver_token = resp.json()["access_token"]
        driver_headers = {"Authorization": f"Bearer {driver_token}"}
        
        # Get Driver ID
        resp = await client.get(f"{USER_SERVICE_URL}/api/v1/users/me", headers=driver_headers)
        if resp.status_code != 200:
             print(f"Driver ID fetch failed: {resp.text}")
             sys.exit(1)
        driver_id = resp.json()["id"]
        print(f"✅ Driver created: {driver_email} ({driver_id})")

        print("Waiting 30s to respect rate limits...")
        await asyncio.sleep(30)

        # 2. Create/Login Passenger
        print("\nStep 2: Setting up Passenger...")
        passenger_email = f"passenger_{uuid.uuid4().hex[:8]}@example.com"
        passenger_data = {
            "email": passenger_email,
            "password": "password123",
            "full_name": "Test Passenger",
            "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"
        }
        
        resp = await client.post(f"{USER_SERVICE_URL}/api/v1/users/", json=passenger_data)
        if resp.status_code not in [200, 201]:
             print(f"Passenger registration failed: {resp.text}")
             sys.exit(1)

        resp = await client.post(f"{USER_SERVICE_URL}/api/v1/auth/login/access-token", data={
            "username": passenger_email,
            "password": "password123"
        })
        if resp.status_code != 200:
             print(f"Passenger login failed: {resp.text}")
             sys.exit(1)

        passenger_token = resp.json()["access_token"]
        passenger_headers = {"Authorization": f"Bearer {passenger_token}"}
        
        resp = await client.get(f"{USER_SERVICE_URL}/api/v1/users/me", headers=passenger_headers)
        passenger_id = resp.json()["id"]
        print(f"✅ Passenger created: {passenger_email} ({passenger_id})")

        # 3. Create Ride
        print("\nStep 3: Creating Ride...")
        ride_data = {
            "origin": {"address": "San Jose State University", "lat": 37.3352, "lng": -121.8811},
            "destination": {"address": "San Francisco International Airport", "lat": 37.6213, "lng": -122.3790},
            "departure_time": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "available_seats": 4,
            "price_per_seat": 15.00,
            "vehicle": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "license_plate": "ABC1234",
                "color": "Silver"
            }
        }
        resp = await client.post(f"{RIDE_SERVICE_URL}/api/v1/rides/", json=ride_data, headers=driver_headers)
        if resp.status_code != 201:
            print(f"❌ Failed to create ride: {resp.text}")
            sys.exit(1)
        ride = resp.json()
        ride_id = ride["id"]
        print(f"✅ Ride created: {ride_id}")

        # 4. Book Ride
        print("\nStep 4: Booking Ride...")
        booking_data = {
            "ride_id": ride_id,
            "pickup_location": {"address": "SJSU", "lat": 37.3352, "lng": -121.8811},
            "dropoff_location": {"address": "SFO", "lat": 37.6213, "lng": -122.3790},
            "seats_booked": 1,
            "payment_method_id": "pm_card_visa" # Test ID
        }
        resp = await client.post(f"{BOOKING_SERVICE_URL}/api/v1/bookings/", json=booking_data, headers=passenger_headers)
        if resp.status_code != 201:
            print(f"❌ Failed to book ride: {resp.text}")
            sys.exit(1)
        booking = resp.json()
        booking_id = booking["id"]
        print(f"✅ Ride booked: {booking_id}")

        # 5. Approve Booking (Driver)
        if booking['status'] == 'pending':
             print("Approving booking...")
             resp = await client.post(f"{BOOKING_SERVICE_URL}/api/v1/bookings/{booking_id}/approve", headers=driver_headers)
             if resp.status_code != 200:
                  print(f"Warning: Could not approve booking: {resp.text}")
             else:
                  print("✅ Booking approved")

        print("\nStep 5: Completing Ride...")
        # Start/Complete Ride
        await client.put(f"{RIDE_SERVICE_URL}/api/v1/rides/{ride_id}/start", headers=driver_headers)
        await client.put(f"{RIDE_SERVICE_URL}/api/v1/rides/{ride_id}/complete", headers=driver_headers)

        # Complete Booking (Explicitly)
        print("Completing Booking...")
        resp = await client.post(f"{BOOKING_SERVICE_URL}/api/v1/bookings/{booking_id}/complete", headers=driver_headers)
        if resp.status_code == 200:
                print("✅ Booking marked as completed")
        else:
                print(f"Warning: Could not complete booking: {resp.text}")

        # 7. Rate Passenger (Driver -> Passenger)
        print("\nStep 6: Driver Rating Passenger...")
        rating_data = {
            "booking_id": booking_id,
            "rating": 5,
            "review": "Great passenger, on time!",
            "punctuality_rating": 5,
            "communication_rating": 5
        }
        resp = await client.post(f"{BOOKING_SERVICE_URL}/api/v1/ratings/", json=rating_data, headers=driver_headers)
        if resp.status_code == 201:
            print("✅ Driver successfully rated passenger!")
        else:
            print(f"❌ Driver failed to rate passenger: {resp.text}")
            sys.exit(1)

        # 8. Rate Driver (Passenger -> Driver)
        print("\nStep 7: Passenger Rating Driver...")
        rating_data = {
            "booking_id": booking_id,
            "rating": 4,
            "review": "Good ride, but music was loud.",
            "cleanliness_rating": 4,
            "communication_rating": 5
        }
        resp = await client.post(f"{BOOKING_SERVICE_URL}/api/v1/ratings/", json=rating_data, headers=passenger_headers)
        if resp.status_code == 201:
            print("✅ Passenger successfully rated driver!")
        else:
            print(f"❌ Passenger failed to rate driver: {resp.text}")
            sys.exit(1)

        # 9. Verify Stats (User Service)
        print("\nStep 8: Verifying User Stats...")
        
        # Check Driver Stats
        resp = await client.get(f"{USER_SERVICE_URL}/api/v1/users/{driver_id}", headers=driver_headers)
        driver_user = resp.json()
        print(f"Driver Stats: Rating={driver_user.get('average_rating_as_driver')}, Count={driver_user.get('total_ratings_as_driver')}")
        
        if driver_user.get('total_ratings_as_driver') == 1 and driver_user.get('average_rating_as_driver') == 4.0:
            print("✅ Driver stats verified!")
        else:
            print("❌ Driver stats incorrect!")

        # Check Passenger Stats
        resp = await client.get(f"{USER_SERVICE_URL}/api/v1/users/{passenger_id}", headers=passenger_headers)
        pass_user = resp.json()
        print(f"Passenger Stats: Rating={pass_user.get('average_rating_as_passenger')}, Count={pass_user.get('total_ratings_as_passenger')}")
        
        if pass_user.get('total_ratings_as_passenger') == 1 and pass_user.get('average_rating_as_passenger') == 5.0:
            print("✅ Passenger stats verified!")
        else:
            print("❌ Passenger stats incorrect!")

if __name__ == "__main__":
    asyncio.run(main())
