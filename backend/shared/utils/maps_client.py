import googlemaps
from typing import Optional, Dict, Any, List
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MapsClient:
    """
    Async wrapper for Google Maps Platform Client.
    Uses ThreadPoolExecutor because the official python client is synchronous.
    """
    def __init__(self, api_key: str, enabled: bool = True):
        self.enabled = enabled
        self.client = None
        if enabled and api_key:
            try:
                self.client = googlemaps.Client(key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps client: {e}")
                self.enabled = False
        else:
            self.enabled = False
            if not api_key:
                logger.warning("Google Maps API Key missing. Maps features disabled.")

        self._executor = ThreadPoolExecutor(max_workers=3)

    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Convert address to valid coordinates and formatted address.
        Returns: {"lat": float, "lng": float, "formatted_address": str} or None.
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            # Run blocking call in thread
            results = await loop.run_in_executor(
                self._executor, 
                lambda: self.client.geocode(address)
            )
            
            if not results:
                return None
            
            # Extract first result
            data = results[0]
            location = data['geometry']['location']
            
            return {
                "lat": location['lat'],
                "lng": location['lng'],
                "formatted_address": data['formatted_address'],
                "place_id": data.get('place_id')
            }
        except Exception as e:
            logger.error(f"Geocode error for '{address}': {e}")
            return None

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to formatted address.
        """
        if not self.enabled or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor,
                lambda: self.client.reverse_geocode((lat, lng))
            )
            
            if not results:
                return None
            
            return results[0]['formatted_address']
        except Exception as e:
            logger.error(f"Reverse geocode error for {lat},{lng}: {e}")
            return None

    async def calculate_route(self, origin: str, destination: str) -> Optional[Dict[str, Any]]:
        """
        Calculate route between two points (address or "lat,lng" string).
        Returns distance (meters), duration (seconds), polyline.
        """
        if not self.enabled or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor,
                lambda: self.client.directions(
                    origin, 
                    destination,
                    mode="driving",
                    units="metric"
                )
            )
            
            if not results:
                return None
                
            route = results[0]
            leg = route['legs'][0]
            
            return {
                "distance_value": leg['distance']['value'], # meters
                "distance_text": leg['distance']['text'],
                "duration_value": leg['duration']['value'], # seconds
                "duration_text": leg['duration']['text'],
                "start_address": leg['start_address'],
                "end_address": leg['end_address'],
                "polyline": route['overview_polyline']['points']
            }
        except Exception as e:
            logger.error(f"Route calculation error: {e}")
            return None
