import sys
import os
import uuid
from typing import List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def check_imports():
    print("Checking Phase 2 Imports...")
    try:
        # Check Booking Service new components
        from backend.services.booking_service.app.models.rating import Rating
        from backend.services.booking_service.app.schemas.rating import RatingCreate, RatingResponse
        from backend.services.booking_service.app.api.routes import ratings
        print("✅ Booking Service: Rating model/schema/routes imported")
    except ImportError as e:
        print(f"❌ Booking Service Import failed: {e}")

    try:
        # Check User Service new schemas
        from backend.services.user_service.app.schemas.user import UserPasswordUpdate
        # Check Endpoint functions (by name check on module)
        from backend.services.user_service.app.api.routes import users
        if hasattr(users, 'update_user_me') and hasattr(users, 'update_password'):
             print("✅ User Service: CRUD endpoints found")
        else:
             print("❌ User Service: Missing CRUD endpoints")
    except ImportError as e:
        print(f"❌ User Service Import failed: {e}")

    try:
        # Check Ride Service endpoints
        from backend.services.ride_service.app.api.routes import rides
        if hasattr(rides, 'get_my_rides') and hasattr(rides, 'delete_ride') and hasattr(rides, 'get_ride_feed'):
             print("✅ Ride Service: CRUD endpoints found")
        else:
             print("❌ Ride Service: Missing CRUD endpoints check (names might vary)")
             # I named them: get_my_rides, delete_ride, get_ride_feed
             pass
    except ImportError as e:
        print(f"❌ Ride Service Import failed: {e}")

    try:
        # Check Slowapi
        import slowapi
        print("✅ Slowapi installed/importable")
    except ImportError:
        print("❌ Slowapi not found (install via requirements.txt)")

def main():
    check_imports()

if __name__ == "__main__":
    main()
