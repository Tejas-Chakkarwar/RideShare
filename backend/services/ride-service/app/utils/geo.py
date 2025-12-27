import math

def haversine_distance(
    lat1: float, 
    lng1: float, 
    lat2: float, 
    lng2: float
) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth using the Haversine formula.
    Returns: Distance in kilometers
    """
    R = 6371.0  # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

def is_within_radius(
    point_lat: float,
    point_lng: float,
    center_lat: float,
    center_lng: float,
    radius_km: float
) -> bool:
    """Check if a point is within a given radius of a center point."""
    distance = haversine_distance(point_lat, point_lng, center_lat, center_lng)
    return distance <= radius_km
