"""
SJSU Campus Locations Database
Curated list of common SJSU buildings and landmarks for quick ride location selection
"""

SJSU_BUILDINGS = [
    {
        "id": "dmh",
        "name": "Duncan Hall",
        "full_name": "Duncan Hall (Engineering)",
        "lat": 37.3327,
        "lng": -121.8816,
        "category": "academic",
        "icon": "school"
    },
    {
        "id": "mlk",
        "name": "MLK Library",
        "full_name": "Dr. Martin Luther King, Jr. Library",
        "lat": 37.3357,
        "lng": -121.8849,
        "category": "library",
        "icon": "library"
    },
    {
        "id": "student_union",
        "name": "Student Union",
        "full_name": "SJSU Student Union",
        "lat": 37.3365,
        "lng": -121.8813,
        "category": "student_services",
        "icon": "restaurant"
    },
    {
        "id": "tower_hall",
        "name": "Tower Hall",
        "full_name": "Tower Hall (Administration)",
        "lat": 37.3352,
        "lng": -121.8813,
        "category": "administration",
        "icon": "office"
    },
    {
        "id": "business",
        "name": "Business Building",
        "full_name": "Lucas Graduate School of Business",
        "lat": 37.3369,
        "lng": -121.8815,
        "category": "academic",
        "icon": "school"
    },
    {
        "id": "sweeney_hall",
        "name": "Sweeney Hall",
        "full_name": "Sweeney Hall",
        "lat": 37.3342,
        "lng": -121.8828,
        "category": "academic",
        "icon": "school"
    },
    {
        "id": "spartan_complex",
        "name": "Spartan Complex",
        "full_name": "Spartan Recreation Center",
        "lat": 37.3333,
        "lng": -121.8798,
        "category": "recreation",
        "icon": "fitness_center"
    },
    {
        "id": "sjsu_stadium",
        "name": "CEFCU Stadium",
        "full_name": "CEFCU Stadium (Football)",
        "lat": 37.3212,
        "lng": -121.8631,
        "category": "sports",
        "icon": "sports_football"
    },
    # Parking lots
    {
        "id": "north_garage",
        "name": "North Parking Garage",
        "full_name": "North Parking Garage",
        "lat": 37.3371,
        "lng": -121.8818,
        "category": "parking",
        "icon": "local_parking"
    },
    {
        "id": "south_garage",
        "name": "South Parking Garage",
        "full_name": "South Parking Garage",
        "lat": 37.3325,
        "lng": -121.8815,
        "category": "parking",
        "icon": "local_parking"
    },
    {
        "id": "west_garage",
        "name": "West Parking Garage",
        "full_name": "West Parking Garage (10th Street)",
        "lat": 37.3338,
        "lng": -121.8838,
        "category": "parking",
        "icon": "local_parking"
    },
    # Popular off-campus locations
    {
        "id": "diridon_station",
        "name": "Diridon Station",
        "full_name": "San Jose Diridon Station (Caltrain/VTA)",
        "lat": 37.3297,
        "lng": -121.9026,
        "category": "transit",
        "icon": "train"
    },
    {
        "id": "sjo_airport",
        "name": "SJC Airport",
        "full_name": "San Jose International Airport",
        "lat": 37.3639,
        "lng": -121.9289,
        "category": "transit",
        "icon": "flight"
    },
]


# Categorized for easy filtering
CATEGORIES = {
    "academic": "Academic Buildings",
    "library": "Libraries",
    "student_services": "Student Services",
    "administration": "Administration",
    "recreation": "Recreation & Sports",
    "sports": "Sports Venues",
    "parking": "Parking",
    "transit": "Transit Hubs",
    "dining": "Dining",
}


def get_sjsu_locations(category: str = None) -> list:
    """
    Get SJSU campus locations, optionally filtered by category.

    Args:
        category: Filter by category (academic, parking, etc.)

    Returns:
        List of location dicts
    """
    if category:
        return [loc for loc in SJSU_BUILDINGS if loc["category"] == category]
    return SJSU_BUILDINGS


def search_sjsu_locations(query: str) -> list:
    """
    Search SJSU locations by name.

    Args:
        query: Search query (e.g., "library", "parking", "duncan")

    Returns:
        Matching locations
    """
    query_lower = query.lower()
    return [
        loc for loc in SJSU_BUILDINGS
        if query_lower in loc["name"].lower()
        or query_lower in loc["full_name"].lower()
    ]
