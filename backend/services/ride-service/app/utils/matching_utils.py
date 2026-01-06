import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class MatchingConfig:
    # Weights (Total = 100)
    ROUTE_SCORE_WEIGHT = 40
    TIME_SCORE_WEIGHT = 20
    PRICE_SCORE_WEIGHT = 15
    RATING_SCORE_WEIGHT = 15
    PREFERENCE_SCORE_WEIGHT = 10
    
    # Thresholds
    MAX_DETOUR_KM = 15.0
    MAX_DETOUR_MINUTES = 20
    MAX_PICKUP_DROPOFF_DISTANCE_KM = 5.0
    DIRECTION_TOLERANCE_DEGREES = 45.0

def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate initial bearing between two points.
    Returns degrees 0-360.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    diff_lng_rad = math.radians(lng2 - lng1)
    
    x = math.sin(diff_lng_rad) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(diff_lng_rad))
    
    initial_bearing = math.atan2(x, y)
    initial_bearing_deg = math.degrees(initial_bearing)
    
    return (initial_bearing_deg + 360) % 360

def check_direction_alignment(
    driver_origin_lat: float, driver_origin_lng: float,
    driver_dest_lat: float, driver_dest_lng: float,
    passenger_dest_lat: float, passenger_dest_lng: float,
    tolerance: float = MatchingConfig.DIRECTION_TOLERANCE_DEGREES
) -> bool:
    """
    Check if driver destination is generally in the same direction 
    relative to driver origin as the passenger destination.
    """
    bearing_driver = calculate_bearing(driver_origin_lat, driver_origin_lng, driver_dest_lat, driver_dest_lng)
    bearing_passenger = calculate_bearing(driver_origin_lat, driver_origin_lng, passenger_dest_lat, passenger_dest_lng)
    
    diff = abs(bearing_driver - bearing_passenger)
    if diff > 180:
        diff = 360 - diff
        
    return diff <= tolerance

def calculate_route_score(detour_km: float) -> float:
    """
    Calculate score (0-40) based on detour distance.
    0 km -> 40 pts
    5 km -> 30 pts
    10 km -> 20 pts
    > 15 km -> 0 pts
    """
    if detour_km > MatchingConfig.MAX_DETOUR_KM:
        return 0.0
    
    # Linear interpolation or steps? Steps are simpler as per plan.
    if detour_km <= 0.5: # Allow small margin for "zero"
        return 40.0
    elif detour_km <= 5.0:
        return 35.0
    elif detour_km <= 10.0:
        return 30.0
    elif detour_km <= 15.0:
        return 20.0
    
    return 0.0

def calculate_time_score(time_diff_minutes: float) -> float:
    """
    Calculate score (0-20) based on time difference.
    """
    if time_diff_minutes <= 5: # "Exact" match tolerance
        return 20.0
    elif time_diff_minutes <= 15:
        return 15.0
    elif time_diff_minutes <= 30:
        return 10.0
    elif time_diff_minutes <= 60:
        return 5.0
    return 0.0

def calculate_price_score(price: float) -> float:
    """
    Calculate score (0-15) based on price.
    Assuming absolute price logic from requirements.
    """
    if price == 0:
        return 15.0
    elif price < 5.0:
        return 12.0
    elif price <= 10.0:
        return 8.0
    elif price <= 20.0:
        return 5.0
    return 2.0

def calculate_rating_score(rating: float) -> float:
    """
    Calculate score (0-15) based on driver rating.
    """
    if rating >= 5.0:
        return 15.0
    elif rating >= 4.5:
        return 12.0
    elif rating >= 4.0:
        return 8.0
    elif rating >= 3.5:
        return 5.0
    return 2.0

def calculate_preference_score(ride_prefs: Optional[Dict[str, Any]], passenger_prefs: Optional[Dict[str, Any]]) -> float:
    """
    Calculate score (0-10) based on preferences.
    """
    if not ride_prefs or not passenger_prefs:
        return 7.0 # Neutral if no prefs
        
    matches = 0
    total = 0
    conflict = False
    
    for key, val in passenger_prefs.items():
        total += 1
        if key in ride_prefs:
            if ride_prefs[key] == val:
                matches += 1
            else:
                conflict = True # Hard conflict logic? Or just mismatch?
                # Requirement says "Conflicting preferences: 0 points"
                # Let's assume strict check for now.
    
    if conflict:
        return 0.0
        
    if total == 0:
        return 7.0
        
    if matches == total:
        return 10.0
    
    return 5.0 # Partial

def calculate_total_score(
    detour_km: float,
    time_diff_minutes: float,
    price: float,
    rating: float,
    ride_prefs: Optional[Dict],
    passenger_prefs: Optional[Dict]
) -> Dict[str, Any]:
    
    route_s = calculate_route_score(detour_km)
    time_s = calculate_time_score(time_diff_minutes)
    price_s = calculate_price_score(price)
    rating_s = calculate_rating_score(rating)
    pref_s = calculate_preference_score(ride_prefs, passenger_prefs)
    
    total = route_s + time_s + price_s + rating_s + pref_s
    
    return {
        "total_score": round(total, 1),
        "breakdown": {
            "route_score": route_s,
            "time_score": time_s,
            "price_score": price_s,
            "rating_score": rating_s,
            "preference_score": pref_s
        }
    }
