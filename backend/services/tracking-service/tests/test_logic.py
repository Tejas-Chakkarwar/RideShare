import pytest
import asyncio
from app.services.eta_service import eta_service
from app.services.geofence_service import geofence_service, GeofenceEvent
from app.websocket.connection_manager import manager
from uuid import uuid4

# Mock WebSocket
class MockWebSocket:
    def __init__(self):
        self.accepted = False
        self.closed = False
    async def accept(self):
        self.accepted = True
    async def close(self, code=1000):
        self.closed = True
    async def send_json(self, data):
        pass
    async def receive_text(self):
        return ""

def test_eta_service():
    async def _test():
        # San Jose to San Francisco (~70km)
        eta = eta_service.calculate_eta(
            current_lat=37.3382,
            current_lng=-121.8863,
            destination_lat=37.7749,
            destination_lng=-122.4194,
            current_speed_kmh=60.0
        )
        assert eta["distance_km"] > 60
        assert eta["distance_km"] < 80
        assert eta["eta_seconds"] > 0
    
    asyncio.run(_test())

def test_geofence_service():
    async def _test():
        ride_id = uuid4()
        
        # 1. Far away
        events = await geofence_service.check_geofence(
            ride_id=ride_id,
            current_lat=37.0000,
            current_lng=-121.0000,
            pickup_lat=37.3382,
            pickup_lng=-121.8863,
            destination_lat=37.7749,
            destination_lng=-122.4194
        )
        assert len(events) == 0
        
        # 2. Approaching pickup (within 500m)
        events = await geofence_service.check_geofence(
            ride_id=ride_id,
            current_lat=37.3382,
            current_lng=-121.8863, # At pickup
            pickup_lat=37.3382,
            pickup_lng=-121.8863,
            destination_lat=37.7749,
            destination_lng=-122.4194
        )
        assert len(events) >= 1
        assert events[0].event_type == "arrived_pickup"
    
    asyncio.run(_test())

def test_connection_manager():
    async def _test():
        ws = MockWebSocket()
        ride_id = "test-ride"
        driver_id = "driver-1"
        
        await manager.connect_driver(ws, ride_id, driver_id)
        assert manager.is_driver_connected(ride_id)
        
        await manager.disconnect_driver(ws, ride_id)
        assert not manager.is_driver_connected(ride_id)
    
    asyncio.run(_test())
