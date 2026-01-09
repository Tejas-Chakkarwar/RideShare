import sys
import os
import uuid
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mocking database session for syntax check
from unittest.mock import MagicMock

def check_imports():
    print("Checking imports...")
    try:
        from backend.services.ride_service.app.models.ride import Ride, RideStatus
        from backend.services.user_service.app.models.document import Document
        from backend.services.booking_service.app.services.booking_service import BookingService
        print("✅ Models and Services imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        # Try adjusting path if strict module structure
        try:
            from backend.services.ride_service.app.models.ride import Ride
            print("✅ Ride model imported")
        except:
             pass

def check_ride_model():
    print("Checking Ride model consistency...")
    from backend.services.ride_service.app.models.ride import Ride, RideStatus
    
    try:
        ride = Ride(
            id=uuid.uuid4(),
            driver_id=uuid.uuid4(), # Should accept UUID now
            status=RideStatus.IN_PROGRESS # Should verify Enum value
        )
        print("✅ Ride model instantiated with UUID driver_id and new Enum status")
    except Exception as e:
        print(f"❌ Ride model check failed: {e}")

def main():
    check_imports()
    # Note: Full verification requires running DB and Services.
    # This script primarily checks static consistency of new changes.

if __name__ == "__main__":
    main()
