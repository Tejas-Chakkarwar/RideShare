import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.services.ride_service import RideService
from app.schemas.ride import RideCreate, LocationSchema, VehicleSchema
from shared.utils.maps_client import MapsClient

# Mock data
params = {
    "origin": {"address": "San Jose State University", "lat": None, "lng": None}, # Missing coords
    "destination": {"address": "San Francisco International Airport", "lat": 37.6213, "lng": -122.3790},
    "departure_time": datetime.now(timezone.utc) + timedelta(days=1),
    "available_seats": 3,
    "price_per_seat": 25.0,
    "vehicle": {
        "make": "Toyota", "model": "Camry", "year": 2020, 
        "license_plate": "7WXYZ", "color": "Blue"
    }
}

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_user_client():
    with patch("app.services.ride_service.user_client") as mock:
        mock.get_user = AsyncMock(return_value={"id": str(uuid4()), "driver_license_verified": True})
        yield mock

@pytest.fixture
def ride_service():
    return RideService()

@pytest.mark.asyncio
async def test_create_ride_auto_geocode(ride_service, mock_db, mock_user_client):
    """Test that creating a ride auto-geocodes the origin when coords are missing"""
    
    # Mock MapsClient
    ride_service.maps_client.enabled = True
    ride_service.maps_client.geocode_address = AsyncMock(return_value={
        "lat": 37.3352, "lng": -121.8811, "formatted_address": "SJSU"
    })
    
    ride_in = RideCreate(**params)
    driver_id = uuid4()
    
    # Create
    ride = await ride_service.create_ride(ride_in, driver_id, mock_db)
    
    # Verify geocode was called
    ride_service.maps_client.geocode_address.assert_called_with("San Jose State University")
    
    # Verify coords were set on the model (checking arguments passed to DB add)
    # Since we don't have a real DB, we check the Ride object constructed
    # But create_ride returns a Ride object, so we check that.
    # The Ride object is created inside the function.
    # Ideally we'd inspect the `db.add` call args or the return value if it's the same object.
    
    assert ride.origin_lat == 37.3352
    assert ride.origin_lng == -121.8811

@pytest.mark.asyncio
async def test_create_ride_maps_disabled_fail(ride_service, mock_db, mock_user_client):
    """Test failure when coords missing and Maps disabled"""
    
    ride_service.maps_client.enabled = False
    
    ride_in = RideCreate(**params)
    driver_id = uuid4()
    
    with pytest.raises(ValueError, match="Coordinates required"):
        await ride_service.create_ride(ride_in, driver_id, mock_db)

@pytest.mark.asyncio
async def test_preview_route(ride_service, mock_db):
    """Test route preview calls MapsClient"""
    
    ride_id = uuid4()
    
    # Mock get_ride return
    mock_ride = MagicMock()
    mock_ride.origin_lat = 37.3352
    mock_ride.origin_lng = -121.8811
    mock_ride.destination_lat = 37.6213
    mock_ride.destination_lng = -122.3790
    
    ride_service.get_ride = AsyncMock(return_value=mock_ride)
    
    # Mock calculate_route
    ride_service.maps_client.calculate_route = AsyncMock(return_value={"distance": "50km"})
    
    result = await ride_service.preview_route(ride_id, mock_db)
    
    assert result == {"distance": "50km"}
    ride_service.maps_client.calculate_route.assert_called_once()
