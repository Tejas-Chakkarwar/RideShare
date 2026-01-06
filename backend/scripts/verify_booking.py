import requests
import json
import time

# Constants
USER_SERVICE_URL = "http://localhost:8001/api/v1/headers" # Verify endpoint? No, auth.
USER_SERVICE_USERS_URL = "http://localhost:8001/api/v1/users"
USER_SERVICE_AUTH_URL = "http://localhost:8001/api/v1/auth"
RIDE_SERVICE_URL = "http://localhost:8002/api/v1/rides"
BOOKING_SERVICE_URL = "http://localhost:8003/api/v1/bookings"
HEADERS = {"Content-Type": "application/json"}

# Dummy Data
USER_DATA = {
    "email": "driver@sjsu.edu",
    "password": "password123",
    "full_name": "Driver Verification",
    "phone_number": "555-0100"
}

RIDE_DATA = {
    "origin": {"address": "San Jose State University"},
    "destination": {"address": "San Francisco"},
    "departure_time": "2024-12-25T10:00:00Z",
    "available_seats": 4,
    "price_per_seat": 25.0,
    "vehicle": {
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "license_plate": "ABC123",
        "color": "Silver"
    }
}

def get_auth_token():
    print("🔑 Authenticating...")
    # 1. Register (Ignore error if exists)
    try:
        requests.post(f"{USER_SERVICE_USERS_URL}/", json=USER_DATA)
    except:
        pass
        
    # 2. Login
    try:
        data = {"username": USER_DATA["email"], "password": USER_DATA["password"]}
        # Using URL encoded form data for OAuth2 usually, but let's see how I implemented it.
        # Section 2 standard: OAuth2PasswordRequestForm expects form data.
        resp = requests.post(f"{USER_SERVICE_AUTH_URL}/login/access-token", data=data)
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            print(f"✅ Authenticated as {USER_DATA['email']}")
            return token
        else:
            print(f"❌ Login Failed: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Auth Connection Error: {e}")
        return None

def verify_booking_flow():
    print("🚀 Starting Booking System Verification...")
    
    token = get_auth_token()
    if not token:
        return
        
    AUTH_HEADERS = HEADERS.copy()
    AUTH_HEADERS["Authorization"] = f"Bearer {token}"

    # 1. Create a Ride
    print("\n1️⃣ Creating a Ride...")
    try:
        resp = requests.post(RIDE_SERVICE_URL, json=RIDE_DATA, headers=AUTH_HEADERS)
        if resp.status_code != 201:
            print(f"❌ Failed to create ride: {resp.text}")
            return
        ride = resp.json()
        ride_id = ride["id"]
        print(f"✅ Ride Created: {ride_id} (Seats: {ride['available_seats']})")
    except Exception as e:
        print(f"❌ Connection Error (Ride Service): {e}")
        return

    # 2. Book Seats
    print("\n2️⃣ Booking 2 Seats...")
    booking_payload = {
        "ride_id": ride_id,
        "seats_booked": 2,
        "pickup_location": {"address": "SJSU", "lat": 37.3352, "lng": -121.8811},
        "dropoff_location": {"address": "SF", "lat": 37.7749, "lng": -122.4194},
        "passenger_notes": "Two of us!"
    }
    
    try:
        # Booking service in dev mode has fake auth dependency, so HEADERS is fine, 
        # OR we can pass AUTH_HEADERS just in case (e.g. if we implemented JWT verification).
        # Section 6 Plan says "Dummy Auth" so no token needed, but passing it won't hurt.
        resp = requests.post(BOOKING_SERVICE_URL, json=booking_payload, headers=HEADERS)
        if resp.status_code != 201:
            print(f"❌ Failed to create booking: {resp.text}")
            return
        booking = resp.json()
        booking_id = booking["id"]
        print(f"✅ Booking Created: {booking_id} (Status: {booking['status']})")
    except Exception as e:
        print(f"❌ Connection Error (Booking Service): {e}")
        return

    # 3. Verify Seat Decrement
    print("\n3️⃣ Verifying Seat Inventory...")
    try:
        # Ride service needs auth
        resp = requests.get(f"{RIDE_SERVICE_URL}/{ride_id}", headers=AUTH_HEADERS)
        ride_updated = resp.json()
        print(f"🔍 Initial Seats: {ride['available_seats']}")
        print(f"🔍 Current Seats: {ride_updated['available_seats']}")
        
        expected_seats = ride['available_seats'] - 2
        if ride_updated['available_seats'] == expected_seats:
            print(f"✅ SUCCESS: Seats correctly decremented to {expected_seats}")
        else:
            print(f"❌ FAILURE: Expected {expected_seats}, got {ride_updated['available_seats']}")
    except Exception as e:
        print(f"❌ Error checking ride: {e}")

    # 4. Approve Booking
    print("\n4️⃣ Approving Booking...")
    try:
        resp = requests.post(f"{BOOKING_SERVICE_URL}/{booking_id}/approve", headers=HEADERS)

        if resp.status_code == 200:
            booking_updated = resp.json()
            print(f"✅ Booking Approved: {booking_updated['status']}")
        else:
            print(f"❌ Failed to approve: {resp.text}")
    except Exception as e:
        print(f"❌ Error approving booking: {e}")

    print("\n🎉 Verification Complete! 🚀")

if __name__ == "__main__":
    verify_booking_flow()
