from fastapi import WebSocket
from typing import Dict, Set, Optional
from uuid import UUID
import logging
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for drivers and passengers
    Handles broadcasting, disconnections, and connection state
    """
    
    def __init__(self):
        # ride_id -> set of passenger websockets
        self.passenger_connections: Dict[str, Set[WebSocket]] = {}
        
        # ride_id -> driver websocket
        self.driver_connections: Dict[str, WebSocket] = {}
        
        # websocket -> user info
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect_driver(
        self,
        websocket: WebSocket,
        ride_id: str,
        driver_id: str
    ):
        """Connect driver for a ride"""
        await websocket.accept()
        
        # Disconnect existing driver if any
        if ride_id in self.driver_connections:
            old_ws = self.driver_connections[ride_id]
            await self.disconnect_driver(old_ws, ride_id)
        
        self.driver_connections[ride_id] = websocket
        self.connection_info[websocket] = {
            "type": "driver",
            "ride_id": ride_id,
            "user_id": driver_id
        }
        
        logger.info(f"Driver {driver_id} connected to ride {ride_id}")
    
    async def connect_passenger(
        self,
        websocket: WebSocket,
        ride_id: str,
        passenger_id: str
    ):
        """Connect passenger to track a ride"""
        await websocket.accept()
        
        if ride_id not in self.passenger_connections:
            self.passenger_connections[ride_id] = set()
        
        self.passenger_connections[ride_id].add(websocket)
        self.connection_info[websocket] = {
            "type": "passenger",
            "ride_id": ride_id,
            "user_id": passenger_id
        }
        
        logger.info(f"Passenger {passenger_id} connected to ride {ride_id}")
    
    async def disconnect_driver(self, websocket: WebSocket, ride_id: str):
        """Disconnect driver"""
        if ride_id in self.driver_connections:
            if self.driver_connections[ride_id] == websocket:
                del self.driver_connections[ride_id]
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"Driver disconnected from ride {ride_id}")
    
    async def disconnect_passenger(self, websocket: WebSocket, ride_id: str):
        """Disconnect passenger"""
        if ride_id in self.passenger_connections:
            self.passenger_connections[ride_id].discard(websocket)
            
            # Clean up empty sets
            if not self.passenger_connections[ride_id]:
                del self.passenger_connections[ride_id]
        
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"Passenger disconnected from ride {ride_id}")
    
    async def broadcast_to_passengers(
        self,
        ride_id: str,
        message: dict
    ):
        """Broadcast location update to all passengers of a ride"""
        if ride_id not in self.passenger_connections:
            return
        
        dead_connections = set()
        
        for websocket in self.passenger_connections[ride_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to passenger: {e}")
                dead_connections.add(websocket)
        
        # Remove dead connections
        for ws in dead_connections:
            await self.disconnect_passenger(ws, ride_id)
    
    def get_passenger_count(self, ride_id: str) -> int:
        """Get number of connected passengers for a ride"""
        return len(self.passenger_connections.get(ride_id, set()))
    
    def is_driver_connected(self, ride_id: str) -> bool:
        """Check if driver is connected"""
        return ride_id in self.driver_connections
    
    async def send_to_driver(self, ride_id: str, message: dict):
        """Send message to driver"""
        if ride_id in self.driver_connections:
            try:
                await self.driver_connections[ride_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to driver: {e}")
    
    def get_active_rides(self) -> list:
        """Get list of rides with active tracking"""
        return list(set(
            list(self.driver_connections.keys()) +
            list(self.passenger_connections.keys())
        ))

# Global connection manager
manager = ConnectionManager()
