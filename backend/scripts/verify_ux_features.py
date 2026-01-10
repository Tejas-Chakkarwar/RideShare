import asyncio
import httpx
import uuid
import sys
import logging
from datetime import datetime, timedelta, timezone

# Configuration
USER_SERVICE_URL = "http://localhost:8001/api/v1/users"
AUTH_SERVICE_URL = "http://localhost:8001/api/v1/auth"
RIDE_SERVICE_URL = "http://localhost:8002/api/v1/rides/templates"
RIDE_BASE_URL = "http://localhost:8002/api/v1/rides"
BOOKING_SERVICE_URL = "http://localhost:8003/api/v1/bookings"
DASHBOARD_URL = "http://localhost:8003/api/v1/dashboard"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_saved_locations():
    logger.info("🚀 Starting Saved Locations Verification...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create User
        email = f"ux_tester_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        user_payload = {"email": email, "password": password, "full_name": "UX Tester", "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"}
        
        resp = await client.post(f"{USER_SERVICE_URL}/", json=user_payload)
        if resp.status_code != 200: logger.error(f"User Create Failed: {resp.text}"); sys.exit(1)
        
        response = await client.post(f"{AUTH_SERVICE_URL}/login/access-token", data={"username": email, "password": password})
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # CRUD
        response = await client.post(f"{USER_SERVICE_URL}/me/saved-locations/", json={"name": "Home", "address": "123 Main St", "lat": 37.3382, "lng": -121.8863, "category": "home"}, headers=headers)
        if response.status_code != 201: logger.error("Create Loc Failed"); sys.exit(1)
        loc_id = response.json()["id"]
        
        response = await client.get(f"{USER_SERVICE_URL}/me/saved-locations/", headers=headers)
        if len(response.json()) != 1: logger.error("List Loc Failed"); sys.exit(1)
        
        await client.delete(f"{USER_SERVICE_URL}/me/saved-locations/{loc_id}", headers=headers)
        logger.info("🎉 Saved Locations Passed!")

async def test_ride_templates():
    logger.info("🚀 Starting Ride Templates Verification...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create Driver
        email = f"driver_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        await client.post(f"{USER_SERVICE_URL}/", json={"email": email, "password": password, "full_name": "Driver", "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"})
        response = await client.post(f"{AUTH_SERVICE_URL}/login/access-token", data={"username": email, "password": password})
        token = response.json()["access_token"]
        
        response = await client.get(f"{USER_SERVICE_URL}/me", headers={"Authorization": f"Bearer {token}"})
        user_id = response.json()["id"]
        headers = {"Authorization": f"Bearer {token}", "X-User-ID": user_id}
        
        # Create Template
        response = await client.post(f"{RIDE_SERVICE_URL}/", json={"name": "Commute", "template_data": {"origin": "Home", "destination": "Work"}}, headers=headers)
        if response.status_code != 201: logger.error("Create Tpl Failed"); sys.exit(1)
        tpl_id = response.json()["id"]
        
        await client.delete(f"{RIDE_SERVICE_URL}/{tpl_id}", headers=headers)
        logger.info("🎉 Ride Templates Passed!")

async def test_advanced_search():
    logger.info("🚀 Starting Advanced Search Verification...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create Driver with Gender
        email = f"driver_m_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        await client.post(f"{USER_SERVICE_URL}/", json={"email": email, "password": password, "full_name": "Male Driver", "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"})
        response = await client.post(f"{AUTH_SERVICE_URL}/login/access-token", data={"username": email, "password": password})
        token = response.json()["access_token"]
        headers_auth = {"Authorization": f"Bearer {token}"}
        await client.put(f"{USER_SERVICE_URL}/me", json={"gender": "male"}, headers=headers_auth)
        
        response = await client.get(f"{USER_SERVICE_URL}/me", headers=headers_auth)
        user_id = response.json()["id"]
        headers = {"Authorization": f"Bearer {token}", "X-User-ID": user_id}
        
        # Create Ride
        ride_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        ride_payload = {
            "origin": {"address": "123 Origin St", "lat": 1, "lng": 1}, 
            "destination": {"address": "456 Dest St", "lat": 2, "lng": 2},
            "departure_time": ride_time, "available_seats": 3, "price_per_seat": 10,
            "vehicle": {"make": "Car", "model": "Model", "year": 2020, "license_plate": "ABC", "color": "Red"}
        }
        resp = await client.post(f"{RIDE_BASE_URL}/", json=ride_payload, headers=headers)
        if resp.status_code != 201: logger.error(f"Create Ride Failed: {resp.text}"); sys.exit(1)
        
        # Search
        response = await client.get(f"{RIDE_BASE_URL}/?driver_gender=male", headers=headers)
        if len(response.json()) == 0: logger.error("Search Male Failed"); sys.exit(1)
        
        response = await client.get(f"{RIDE_BASE_URL}/?driver_gender=female", headers=headers)
        if len(response.json()) > 0: logger.error("Search Female Failed (Found Mismatched)"); sys.exit(1)
        
        logger.info("🎉 Advanced Search Passed!")

async def test_ride_history_and_dashboard():
    logger.info("🚀 Starting History & Dashboard Verification...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create Driver and Passenger
        d_email = f"dash_driver_{uuid.uuid4().hex[:8]}@example.com"
        p_email = f"receipt_pax_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        
        # Driver
        d_create_resp = await client.post(f"{USER_SERVICE_URL}/", json={"email": d_email, "password": password, "full_name": "Dash Driver", "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"})
        if d_create_resp.status_code != 200: logger.error(f"Drive Create Failed: {d_create_resp.text}"); sys.exit(1)
        
        # Sleep to avoid rate limit (creation limit)
        await asyncio.sleep(5) 

        d_resp = await client.post(f"{AUTH_SERVICE_URL}/login/access-token", data={"username": d_email, "password": password})
        d_token = d_resp.json()["access_token"]
        d_headers = {"Authorization": f"Bearer {d_token}"}
        d_id = (await client.get(f"{USER_SERVICE_URL}/me", headers=d_headers)).json()["id"]
        d_headers["X-User-ID"] = d_id
        
        # Passenger
        p_create_resp = await client.post(f"{USER_SERVICE_URL}/", json={"email": p_email, "password": password, "full_name": "Receipt Pax", "phone_number": f"+1{uuid.uuid4().int % 10000000000:010d}"})
        if p_create_resp.status_code != 200: logger.error(f"Pax Create Failed: {p_create_resp.text}"); sys.exit(1)

        p_resp = await client.post(f"{AUTH_SERVICE_URL}/login/access-token", data={"username": p_email, "password": password})
        p_token = p_resp.json()["access_token"]
        p_headers = {"Authorization": f"Bearer {p_token}"}
        p_id = (await client.get(f"{USER_SERVICE_URL}/me", headers=p_headers)).json()["id"]
        p_headers["X-User-ID"] = p_id 
        
        # 2. Driver Creates Ride
        ride_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        ride_payload = {
            "origin": {"address": "123 San Jose", "lat": 37, "lng": -121}, 
            "destination": {"address": "456 San Fran", "lat": 37.7, "lng": -122},
            "departure_time": ride_time, "available_seats": 2, "price_per_seat": 50,
            "vehicle": {"make": "Honda", "model": "Civic", "year": 2022, "license_plate": "DASH1", "color": "BK"}
        }
        r_resp = await client.post(f"{RIDE_BASE_URL}/", json=ride_payload, headers=d_headers)
        if r_resp.status_code != 201: logger.error(f"Ride Create Failed: {r_resp.text}"); sys.exit(1)
        ride_id = r_resp.json()["id"]
        
        # 3. Passenger Books Ride
        b_payload = {
            "ride_id": ride_id, "seats_booked": 1, 
            "pickup_location": {"address": "123 San Jose", "lat": 37, "lng": -121},
            "dropoff_location": {"address": "456 San Fran", "lat": 37.7, "lng": -122}
        }
        b_resp = await client.post(f"{BOOKING_SERVICE_URL}/", json=b_payload, headers=p_headers)
        if b_resp.status_code != 201: logger.error(f"Booking Failed: {b_resp.text}"); sys.exit(1)
        booking_id = b_resp.json()["id"]
        
        # 4. Driver Approves
        await client.post(f"{BOOKING_SERVICE_URL}/{booking_id}/approve", headers=d_headers)
        
        # Try Start/Complete (Best effort)
        await client.put(f"{RIDE_BASE_URL}/{ride_id}/start", headers=d_headers)
        await client.put(f"{RIDE_BASE_URL}/{ride_id}/complete", headers=d_headers)
        
        # 5. Verify History (Passenger)
        h_resp = await client.get(f"{BOOKING_SERVICE_URL}/my-bookings", headers=p_headers)
        if h_resp.status_code != 200:
             logger.error(f"History Failed: {h_resp.status_code} - {h_resp.text}")
             sys.exit(1)
        if len(h_resp.json()) == 0: logger.error("History Failed"); sys.exit(1)
        
        # 6. Verify Receipt (Passenger)
        rcpt_resp = await client.get(f"{BOOKING_SERVICE_URL}/{booking_id}/receipt", headers=p_headers)
        if rcpt_resp.status_code != 200: logger.error(f"Receipt Failed: {rcpt_resp.status_code}"); sys.exit(1)
        if rcpt_resp.headers["content-type"] != "application/pdf": logger.error("Receipt not PDF"); sys.exit(1)
        logger.info("✅ Receipt PDF verified")
        
        # 7. Verify Dashboard (Driver)
        dash_resp = await client.get(f"{DASHBOARD_URL}/driver", headers=d_headers)
        if dash_resp.status_code != 200: logger.error(f"Dashboard Failed: {dash_resp.text}"); sys.exit(1)
        data = dash_resp.json()
        logger.info(f"Dashboard Data: {data}")
        logger.info("🎉 History & Dashboard Passed!")

if __name__ == "__main__":
    async def main():
        await test_saved_locations()
        print("Sleeping 60s...")
        await asyncio.sleep(60)
        
        await test_ride_templates()
        print("Sleeping 60s...")
        await asyncio.sleep(60)
        
        await test_advanced_search()
        print("Sleeping 60s...")
        await asyncio.sleep(60)
        
        await test_ride_history_and_dashboard()
    
    asyncio.run(main())
