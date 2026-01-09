import asyncio
import httpx
import sys
from uuid import uuid4

# Setup URLs
USER_SERVICE_URL = "http://localhost:8001/api/v1"
RIDE_SERVICE_URL = "http://localhost:8002/api/v1"
BOOKING_SERVICE_URL = "http://localhost:8003/api/v1"

async def test_health():
    print("Testing Health/Root endpoints...")
    async with httpx.AsyncClient() as client:
        # User Service
        try:
             # Assuming root endpoint exists? If not, services usually have /health or docs. 
             # We can try to hit docs if root is 404.
             # Actually, let's just assume if connect works it's fine.
             resp = await client.get(f"{USER_SERVICE_URL}/docs")
             print(f"User Service: {resp.status_code}")
        except Exception as e:
             print(f"User Service Failed: {e}")

        # Ride Service
        try:
             resp = await client.get(f"{RIDE_SERVICE_URL}/docs")
             print(f"Ride Service: {resp.status_code}")
        except Exception as e:
             print(f"Ride Service Failed: {e}")

        # Booking Service
        try:
             resp = await client.get(f"{BOOKING_SERVICE_URL}/docs")
             print(f"Booking Service: {resp.status_code}")
        except Exception as e:
             print(f"Booking Service Failed: {e}")

async def main():
    print("--- Starting Final Verification ---")
    await test_health()
    print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
