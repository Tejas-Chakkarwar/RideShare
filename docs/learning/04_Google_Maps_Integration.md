# Section 4: Google Maps Platform Integration - Complete Learning Guide

**Prerequisites**: You should have completed reading `00_Complete_Technology_Guide.md` and `02_Advanced_Topics_Migrations_and_Microservices.md` first.

---

## Table of Contents

### Part 1: Google Maps Platform Fundamentals
1. What is Google Maps Platform?
2. Google Maps APIs Overview
3. API Keys and Authentication
4. Quota, Pricing, and Cost Management
5. API Restrictions and Security

### Part 2: Geocoding API
6. What is Geocoding?
7. Forward Geocoding (Address → Coordinates)
8. Reverse Geocoding (Coordinates → Address)
9. Geocoding Response Structure
10. Error Handling in Geocoding

### Part 3: Directions API
11. What is the Directions API?
12. Route Calculation
13. Distance and Duration Information
14. Polyline Encoding
15. Travel Modes and Options

### Part 4: Async Operations with Sync Libraries
16. The Blocking I/O Problem
17. ThreadPoolExecutor Pattern
18. `run_in_executor()` Explained
19. Why Not Just Use Threads Everywhere?

### Part 5: Caching Strategies
20. Why Cache External API Calls?
21. Redis as a Cache Layer
22. Cache Key Design
23. TTL (Time To Live) Strategy
24. Cache Invalidation

### Part 6: MapsClient Implementation
25. File: `shared/utils/maps_client.py` - Architecture
26. Initialization and Configuration
27. Geocode Address Method
28. Reverse Geocode Method
29. Calculate Route Method
30. Error Handling and Logging

### Part 7: CacheManager Implementation
31. File: `shared/utils/cache_manager.py` - Architecture
32. Get Cached Method
33. Set Cached Method
34. Cache Key Generation
35. JSON Serialization

### Part 8: Integration with Ride Service
36. How Ride Service Uses MapsClient
37. Auto-Geocoding in Ride Creation
38. Route Preview Endpoint
39. Fallback When Maps Disabled

### Part 9: Testing External APIs
40. Mocking External Services
41. Test File: `test_maps.py` Walkthrough
42. Unit Testing with AsyncMock
43. Testing Error Scenarios

### Part 10: Real-World Scenarios
44. Cost Optimization Techniques
45. Handling API Rate Limits
46. Graceful Degradation
47. Monitoring and Logging
48. Production Best Practices

---

# Part 1: Google Maps Platform Fundamentals

## 1. What is Google Maps Platform?

### The Simple Explanation
Google Maps Platform is like renting Google's mapping superpowers for your own application. Instead of building your own map system from scratch, you pay Google to use their:
- Address database (billions of addresses worldwide)
- Route calculation algorithms
- Traffic data
- Place information

### Real-World Analogy
Think of it like this:
- **Building your own system** = Building your own delivery truck fleet, hiring drivers, creating routes
- **Using Google Maps Platform** = Calling Uber/DoorDash - you pay per use and they handle all the complexity

### Why We Need It for RideShare
For our carpooling app, we need to:
1. **Convert addresses to coordinates** - User types "San Jose State University", we need to know that's at latitude 37.3352, longitude -121.8811
2. **Calculate routes** - Find the best path from point A to B, how long it takes, how far it is
3. **Validate addresses** - Make sure "123 Fake Street" doesn't get accepted
4. **Show maps** - Display routes visually to users

---

## 2. Google Maps APIs Overview

Google Maps Platform has **18+ different APIs**. We use only 3:

### APIs We Use:

#### **Geocoding API**
- **Purpose**: Convert addresses ↔ coordinates
- **Example Input**: "1 Washington Square, San Jose, CA"
- **Example Output**: `{lat: 37.3352, lng: -121.8811}`
- **Cost**: $5 per 1,000 requests (first $200/month free)

#### **Directions API**
- **Purpose**: Calculate routes between two points
- **Example Input**: Origin = "SJSU", Destination = "SFO Airport"
- **Example Output**: Distance = 78km, Duration = 55 minutes, Route polyline
- **Cost**: $5 per 1,000 requests

#### **Places API** (Future)
- **Purpose**: Autocomplete addresses as user types
- **Example**: User types "San Jo..." → suggests "San Jose State University"
- **Not implemented yet in our code**

### APIs We DON'T Use (But You Should Know About):
- **Maps JavaScript API** - For embedding interactive maps in web pages
- **Distance Matrix API** - Calculate distances for multiple origin/destination pairs
- **Elevation API** - Get altitude at coordinates
- **Time Zone API** - Get timezone for coordinates

---

## 3. API Keys and Authentication

### What is an API Key?

An API key is like a credit card number for using Google's services. Every request you make includes this key so Google knows:
1. **Who you are** - Which project/account to bill
2. **If you're allowed** - Based on restrictions you set
3. **How much you've used** - For billing and quota tracking

### API Key Format
```
AIzaSyD1234567890abcdefGHIJKLMNOPQRSTUVWXYZ
```
- Always starts with `AIzaSy`
- 39 characters long
- Random letters and numbers

### How We Store It (Security)

**WRONG WAY** ❌:
```python
# Hardcoded in code
api_key = "AIzaSyD1234567890abcdefGHIJKLMNOPQRSTUVWXYZ"
```

**RIGHT WAY** ✅:
```python
# In .env file (NOT committed to git)
GOOGLE_MAPS_API_KEY=AIzaSyD1234567890abcdefGHIJKLMNOPQRSTUVWXYZ

# In config.py
class Settings(BaseSettings):
    GOOGLE_MAPS_API_KEY: str = ""

    class Config:
        env_file = ".env"
```

### Why This Matters
If you commit your API key to GitHub:
1. Bots scan GitHub for leaked keys (happens in minutes)
2. They use your key to make millions of requests
3. You get billed thousands of dollars
4. **This happens every day to real developers**

---

## 4. Quota, Pricing, and Cost Management

### Google's Free Tier
Every month, you get **$200 in free credits**. This covers approximately:
- **40,000 geocoding requests** (at $5 per 1,000)
- **40,000 directions requests** (at $5 per 1,000)

### What Happens After Free Tier?
You pay per request:
- Geocoding: $0.005 per request
- Directions: $0.005 per request
- If you make 100,000 geocoding requests = $500

### Cost Optimization Strategies

#### 1. **Caching** (What We Implemented)
Don't call Google for the same request twice:
```python
# First time: User searches "SJSU" → Call Google ($0.005)
# Save result in Redis cache
# Next 1000 users search "SJSU" → Use cache ($0)
# Savings: $5 per 1,000 repeat searches
```

#### 2. **Client-Side Geocoding** (Future)
Let user's browser call Google directly for some features (Google doesn't charge for Maps JavaScript API embed)

#### 3. **Batch Requests**
Use Distance Matrix API to get 100 routes in one request instead of 100 separate Directions API calls

#### 4. **Disable When Not Needed**
Our code has `GOOGLE_MAPS_ENABLED` flag:
```python
# In development without API key
GOOGLE_MAPS_ENABLED=False
# App still works, just requires manual coordinates
```

---

## 5. API Restrictions and Security

### Types of Restrictions

#### **Application Restrictions** (Recommended)
Limit which websites/apps can use your key:

**HTTP Referrer Restriction**:
```
Allowed: rideshare.sjsu.edu/*
Blocked: evil-hacker-site.com
```

**IP Address Restriction**:
```
Allowed: 35.184.123.45 (Your server IP)
Blocked: All other IPs
```

#### **API Restrictions**
Limit which Google APIs this key can access:
```
Allowed APIs:
- Geocoding API
- Directions API
Blocked APIs:
- All other Google APIs
```

### Why Restrictions Matter

**Without Restrictions**:
1. Hacker steals your key
2. Uses it for their completely different app
3. Racks up $10,000 bill on your account

**With Restrictions**:
1. Hacker steals your key
2. Tries to use it from their server
3. Google blocks it because IP doesn't match
4. You're safe

### Our Configuration
```python
# ride-service/app/core/config.py
class Settings(BaseSettings):
    GOOGLE_MAPS_API_KEY: str = ""  # Read from .env
    GOOGLE_MAPS_ENABLED: bool = True  # Toggle to disable
```

---

# Part 2: Geocoding API

## 6. What is Geocoding?

### The Concept
**Geocoding** = Converting human-readable addresses into geographic coordinates

Think of it like translating:
- **Human language**: "1 Washington Square, San Jose, CA 95192"
- **Computer language**: `{latitude: 37.3352, longitude: -121.8811}`

### Why Coordinates Matter

Computers can't understand "near SJSU" but they CAN calculate:
```python
# Distance between two points
distance = haversine(
    lat1=37.3352, lng1=-121.8811,  # SJSU
    lat2=37.7749, lng2=-122.4194   # San Francisco
)
# Result: ~68 km
```

### Two Types of Geocoding

#### Forward Geocoding
Address → Coordinates
```
Input: "San Jose State University"
Output: {lat: 37.3352, lng: -121.8811}
```

#### Reverse Geocoding
Coordinates → Address
```
Input: {lat: 37.3352, lng: -121.8811}
Output: "1 Washington Square, San Jose, CA 95192"
```

---

## 7. Forward Geocoding (Address → Coordinates)

### How It Works

**Step 1**: User provides address (might be incomplete)
```
"san jose state"  (lowercase, incomplete)
```

**Step 2**: Google's algorithm searches their database
- Checks millions of addresses
- Uses fuzzy matching (handles typos)
- Considers context (country, region)

**Step 3**: Returns best matches
```json
{
  "results": [
    {
      "formatted_address": "San Jose State University, San Jose, CA 95192",
      "geometry": {
        "location": {"lat": 37.3352, "lng": -121.8811}
      },
      "place_id": "ChIJ3RwegjnMj4ARj3DFbSD-vJU"
    }
  ]
}
```

### Our Implementation

```python
# shared/utils/maps_client.py

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
```

### Line-by-Line Breakdown

**Lines 30-33**: Function signature
```python
async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
```
- `async def` - This is an async function (can use `await`)
- `address: str` - Input is a string (the address)
- `-> Optional[Dict[str, Any]]` - Returns either a dictionary or `None`

**Lines 35-36**: Check if enabled
```python
if not self.enabled or not self.client:
    return None
```
- If Google Maps is disabled in config → return `None`
- If API key is invalid → return `None`
- This allows app to work even without Google Maps

**Line 39**: Get event loop
```python
loop = asyncio.get_event_loop()
```
- Gets the current async event loop (needed for `run_in_executor`)

**Lines 41-44**: The key part
```python
results = await loop.run_in_executor(
    self._executor,
    lambda: self.client.geocode(address)
)
```
Breaking this down:
- `self.client.geocode(address)` - Google's library function (BLOCKING, not async)
- `lambda: ...` - Wrap it in a lambda function
- `self._executor` - ThreadPoolExecutor (worker threads)
- `loop.run_in_executor(...)` - Run the blocking function in a thread
- `await ...` - Wait for thread to finish without blocking other async operations

**Why this complex pattern?** See Topic 16-17 in Part 4.

**Lines 46-47**: Handle no results
```python
if not results:
    return None
```
If Google found no matches for the address

**Lines 50-51**: Extract data
```python
data = results[0]
location = data['geometry']['location']
```
- `results` is a list of matches, we take first one `[0]`
- Navigate nested structure: `results → [0] → geometry → location`

**Lines 53-57**: Return formatted response
```python
return {
    "lat": location['lat'],
    "lng": location['lng'],
    "formatted_address": data['formatted_address'],
    "place_id": data.get('place_id')
}
```
Clean dictionary with just the data we need

**Lines 58-60**: Error handling
```python
except Exception as e:
    logger.error(f"Geocode error for '{address}': {e}")
    return None
```
If anything goes wrong:
- Log the error (for debugging)
- Return `None` (don't crash the app)

---

## 8. Reverse Geocoding (Coordinates → Address)

### What It's For

**Use Case 1**: User clicks on map
```
User clicks map → Get lat/lng → Convert to address → Display "123 Main St"
```

**Use Case 2**: Mobile GPS
```
Phone GPS → Get current location coordinates → Show "You are at..."
```

**Use Case 3**: Data validation
```
Verify that coordinates 37.3352, -121.8811 actually correspond to a real place
```

### Our Implementation

```python
# shared/utils/maps_client.py

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
```

### Key Differences from Forward Geocoding

**Input**: Tuple of coordinates instead of string
```python
self.client.reverse_geocode((lat, lng))
# Note: (lat, lng) is a tuple - parentheses matter!
```

**Output**: Just the address string (simpler)
```python
return results[0]['formatted_address']
# Instead of full dict with lat, lng, etc.
```

### Real Response Example

**Request**:
```python
reverse_geocode(37.3352, -121.8811)
```

**Google's Response**:
```json
{
  "results": [
    {
      "formatted_address": "1 Washington Square, San Jose, CA 95192, USA",
      "place_id": "ChIJ3RwegjnMj4ARj3DFbSD-vJU",
      "types": ["university", "point_of_interest"]
    },
    {
      "formatted_address": "San Jose, CA 95192, USA",
      "types": ["postal_code"]
    },
    {
      "formatted_address": "San Jose, CA, USA",
      "types": ["locality", "political"]
    }
  ]
}
```

Notice: Multiple results with different levels of detail. We take `[0]` (most specific).

---

## 9. Geocoding Response Structure

### Understanding the Full Response

When Google geocodes an address, you get a LOT of information. Here's the full structure:

```json
{
  "results": [
    {
      "address_components": [
        {"long_name": "1", "short_name": "1", "types": ["street_number"]},
        {"long_name": "Washington Square", "short_name": "Washington Sq", "types": ["route"]},
        {"long_name": "San Jose", "short_name": "San Jose", "types": ["locality"]},
        {"long_name": "Santa Clara County", "short_name": "Santa Clara County", "types": ["administrative_area_level_2"]},
        {"long_name": "California", "short_name": "CA", "types": ["administrative_area_level_1"]},
        {"long_name": "United States", "short_name": "US", "types": ["country"]},
        {"long_name": "95192", "short_name": "95192", "types": ["postal_code"]}
      ],
      "formatted_address": "1 Washington Square, San Jose, CA 95192, USA",
      "geometry": {
        "location": {"lat": 37.3352062, "lng": -121.8810715},
        "location_type": "ROOFTOP",
        "viewport": {
          "northeast": {"lat": 37.3365551802915, "lng": -121.8797225197085},
          "southwest": {"lat": 37.3338572197085, "lng": -121.8824204802915}
        }
      },
      "place_id": "ChIJ3RwegjnMj4ARj3DFbSD-vJU",
      "types": ["university", "point_of_interest", "establishment"]
    }
  ],
  "status": "OK"
}
```

### Breaking Down Each Part

#### **address_components**
Array of parts that make up the address:
```python
{
  "long_name": "California",     # Full name
  "short_name": "CA",             # Abbreviation
  "types": ["administrative_area_level_1"]  # What type of component
}
```

**Common types**:
- `street_number` - Building number
- `route` - Street name
- `locality` - City
- `administrative_area_level_1` - State/Province
- `country` - Country
- `postal_code` - ZIP code

#### **formatted_address**
The complete, human-readable address:
```
"1 Washington Square, San Jose, CA 95192, USA"
```
This is what we display to users.

#### **geometry**
Geographic information:
```json
{
  "location": {"lat": 37.3352062, "lng": -121.8810715},
  "location_type": "ROOFTOP",
  "viewport": {...}
}
```

**location_type** indicates accuracy:
- `ROOFTOP` - Exact address (most precise)
- `RANGE_INTERPOLATED` - Approximate (interpolated between known addresses)
- `GEOMETRIC_CENTER` - Center of area (like a street or city)
- `APPROXIMATE` - Rough estimate

#### **place_id**
Unique identifier for this place:
```
"ChIJ3RwegjnMj4ARj3DFbSD-vJU"
```
- Always the same for this location
- Can be used to reference this place in other Google APIs
- More stable than coordinates (which might change slightly)

#### **types**
Categories for this location:
```json
["university", "point_of_interest", "establishment"]
```

### What We Actually Use

Out of all this data, we only extract:
```python
{
    "lat": location['lat'],                          # 37.3352062
    "lng": location['lng'],                          # -121.8810715
    "formatted_address": data['formatted_address'],  # "1 Washington Square..."
    "place_id": data.get('place_id')                 # "ChIJ3Rwe..."
}
```

**Why not use everything?**
- We only need coordinates for calculations
- Formatted address for display
- Place ID for future features (optional)
- Storing less data = faster database, less memory

---

## 10. Error Handling in Geocoding

### Common Errors and Our Handling

#### Error 1: Invalid Address
```python
geocode_address("asdfghjkl random text")
# Google returns empty results array
```

**Our handling**:
```python
if not results:
    return None  # Caller handles None gracefully
```

#### Error 2: API Key Invalid
```python
# Google throws exception: "REQUEST_DENIED"
```

**Our handling**:
```python
except Exception as e:
    logger.error(f"Geocode error for '{address}': {e}")
    return None
```

#### Error 3: Network Timeout
```python
# Google doesn't respond within timeout
```

**Our handling**:
```python
# Exception caught by try/except
# Returns None
```

#### Error 4: Quota Exceeded
```python
# Google returns "OVER_QUERY_LIMIT"
```

**Our handling**:
```python
# Currently: Exception caught, returns None
# Better: Implement exponential backoff, cache more aggressively
```

### How Ride Service Handles None

When `geocode_address()` returns `None`:

```python
# ride_service.py

if (ride_data.origin.lat is None or ride_data.origin.lng is None):
    if self.maps_client.enabled:
        geo_res = await self.maps_client.geocode_address(ride_data.origin.address)
        if geo_res:
            ride_data.origin.lat = geo_res['lat']
            ride_data.origin.lng = geo_res['lng']
        else:
            # geocode_address returned None
            raise ValueError(f"Could not geocode origin: {ride_data.origin.address}")
    else:
        raise ValueError("Coordinates required for origin when Maps disabled")
```

**Flow**:
1. User submits ride with address but no coordinates
2. Try to geocode address
3. If geocoding fails (`None`) → Raise ValueError
4. ValueError becomes HTTP 400 error in routes
5. User sees: "Could not geocode origin: [address]"

### Logging Strategy

Every error is logged:
```python
logger.error(f"Geocode error for '{address}': {e}")
```

This creates log entries like:
```
ERROR:shared.utils.maps_client:Geocode error for 'invalid address xyz': REQUEST_DENIED
ERROR:shared.utils.maps_client:Geocode error for '': Invalid request (empty address)
```

**Why log?**
- Debug production issues
- Monitor API health
- Detect patterns (lots of timeouts = network issue)
- Alert if quota exceeded

---

# Part 3: Directions API

## 11. What is the Directions API?

### The Concept

The **Directions API** calculates the best route between two locations. It's like having Google Maps's routing engine in your app.

**What it provides**:
1. **Step-by-step directions** - "Turn left on Main St"
2. **Distance** - 42 kilometers
3. **Duration** - 35 minutes
4. **Route geometry** - Encoded polyline for drawing on map
5. **Traffic consideration** - Real-time or typical traffic

### Real-World Analogy

Imagine you hire a professional navigator:
- **You say**: "I need to go from SJSU to SFO Airport"
- **Navigator provides**:
  - Best route to take
  - How long it will take
  - How far it is
  - Turn-by-turn directions
  - Alternative routes

That's exactly what Directions API does, but programmatically.

---

## 12. Route Calculation

### Our Implementation

```python
# shared/utils/maps_client.py

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
```

### Input Formats

The `origin` and `destination` can be:

#### Format 1: Address String
```python
calculate_route(
    origin="San Jose State University",
    destination="San Francisco International Airport"
)
```

#### Format 2: Coordinates String
```python
calculate_route(
    origin="37.3352,-121.8811",
    destination="37.6213,-122.3790"
)
```

#### Format 3: Place ID
```python
calculate_route(
    origin="place_id:ChIJ3RwegjnMj4ARj3DFbSD-vJU",
    destination="place_id:ChIJVVVVVe122YkRsyjhgjh_WUYZ"
)
```

**We use Format 2** (coordinates) in our ride service:
```python
# ride_service.py
origin = f"{ride.origin_lat},{ride.origin_lng}"
destination = f"{ride.destination_lat},{ride.destination_lng}"

return await self.maps_client.calculate_route(origin, destination)
```

**Why coordinates instead of addresses?**
- Faster (no geocoding step)
- More accurate (exact location)
- Cheaper (one API call instead of three: geocode origin, geocode destination, directions)

### Parameters Explained

```python
self.client.directions(
    origin,          # Starting point
    destination,     # Ending point
    mode="driving",  # Travel mode
    units="metric"   # Distance units
)
```

#### **mode** options:
- `"driving"` - Car routes (what we use)
- `"walking"` - Pedestrian routes
- `"bicycling"` - Bike routes
- `"transit"` - Public transportation

#### **units** options:
- `"metric"` - Kilometers, meters (what we use)
- `"imperial"` - Miles, feet

#### Other parameters we DON'T use (but could):
- `departure_time` - For traffic prediction
- `avoid` - Avoid tolls, highways, ferries
- `waypoints` - Intermediate stops
- `alternatives` - Get multiple route options

---

## 13. Distance and Duration Information

### Understanding the Response

```python
{
    "distance_value": 78345,          # Meters (integer)
    "distance_text": "78.3 km",       # Human-readable
    "duration_value": 3312,           # Seconds (integer)
    "duration_text": "55 mins",       # Human-readable
    "start_address": "San Jose State University, San Jose, CA 95192, USA",
    "end_address": "San Francisco International Airport (SFO), San Francisco, CA 94128, USA",
    "polyline": "m~feFbx~Uh@y@BI..."  # Encoded route line
}
```

### Why Two Formats for Each Value?

#### distance_value vs distance_text

**distance_value** (78345 meters):
- **For calculations**: Price = distance_value * $0.50 per km
- **For comparisons**: Is this ride < 100km?
- **For database storage**: Numbers are easier to query

**distance_text** ("78.3 km"):
- **For display to users**: "This ride is 78.3 km"
- **Localized**: Automatically uses user's preferred units
- **User-friendly**: Includes units, rounded appropriately

#### duration_value vs duration_text

**duration_value** (3312 seconds = 55.2 minutes):
- **For calculations**: ETA = departure_time + duration_value
- **For sorting**: Find fastest routes
- **For database**: Store as integer

**duration_text** ("55 mins"):
- **For display**: "Estimated travel time: 55 mins"
- **Contextual**: Could be "1 hour 23 mins" or "2 hours" depending on length
- **Rounded**: User doesn't need "55.2 minutes"

### Real Example from Our App

User creates a ride from SJSU to SFO:

```python
# Ride Service calls
route = await maps_client.calculate_route(
    "37.3352,-121.8811",  # SJSU
    "37.6213,-122.3790"   # SFO
)

# Returns:
{
    "distance_value": 78345,
    "distance_text": "78.3 km",
    "duration_value": 3312,
    "duration_text": "55 mins",
    ...
}

# Frontend displays:
"Distance: 78.3 km"
"Duration: 55 mins"

# Backend calculates price:
price = (route['distance_value'] / 1000) * 0.50  # $0.50 per km
# price = 78.345 * 0.50 = $39.17
```

---

## 14. Polyline Encoding

### What is a Polyline?

A **polyline** is a series of connected line segments that represent a route on a map.

**Without encoding**:
```json
[
  {"lat": 37.3352, "lng": -121.8811},
  {"lat": 37.3360, "lng": -121.8820},
  {"lat": 37.3368, "lng": -121.8829},
  ... (hundreds of points)
]
```

**With encoding** (what Google uses):
```
m~feFbx~Uh@y@BIrADwC@iCDoCF...
```

### Why Encode?

**Size comparison** for a route with 500 points:

| Format | Size |
|--------|------|
| JSON array of coordinates | ~25,000 bytes |
| Encoded polyline | ~1,500 bytes |
| **Savings** | **94% smaller!** |

### How Encoding Works (High Level)

1. **Delta encoding**: Store difference between consecutive points, not absolute coordinates
```
Instead of: [37.3352, 37.3360, 37.3368]
Store: [37.3352, +0.0008, +0.0008]
```

2. **Scale coordinates**: Multiply by 100,000 to remove decimal points
```
37.3352 * 100000 = 3733520
```

3. **Convert to ASCII characters**: Map numbers to printable characters
```
3733520 → "m~fe"
```

**You don't need to understand the algorithm**. Just know:
- Polyline = compressed route geometry
- Can be decoded for display on maps
- Much more efficient than sending raw coordinates

### Using the Polyline

```python
# Our response includes encoded polyline
{
    "polyline": "m~feFbx~Uh@y@BIrADwC@iCDoCF..."
}

# Frontend JavaScript decodes it:
const path = google.maps.geometry.encoding.decodePath(polyline);

// Then draws on map:
new google.maps.Polyline({
    path: path,
    strokeColor: '#FF0000',
    strokeWeight: 3,
    map: map
});
```

### Where We Store It

Currently we don't store polylines in database. Why?
- **Large data**: Even encoded, it's ~1-5KB per route
- **Not queryable**: Can't search/filter by polyline
- **Can regenerate**: Call Directions API when needed

**Future optimization**: Cache polylines in Redis for frequently requested routes.

---

## 15. Travel Modes and Options

### Travel Modes

The `mode` parameter changes routing algorithm:

#### **"driving"** (What We Use)
- Uses roads accessible to cars
- Considers one-way streets
- Avoids pedestrian-only areas
- Accounts for turn restrictions
- **Speed**: Highway speeds, traffic

#### **"walking"**
- Uses sidewalks and pedestrian paths
- Can use stairs, walking trails
- Ignores one-way street restrictions
- **Speed**: ~5 km/h walking pace

#### **"bicycling"**
- Prefers bike lanes and bike-friendly roads
- Avoids highways
- Considers elevation (avoids steep hills when possible)
- **Speed**: ~15-20 km/h biking pace

#### **"transit"**
- Uses public transportation (buses, trains, subway)
- Includes walking to/from stops
- Requires `departure_time` parameter
- **Response includes**: Which bus/train to take, transfer points

### Additional Options

#### **avoid** Parameter
```python
self.client.directions(
    origin,
    destination,
    avoid="tolls"  # or "highways" or "ferries"
)
```

**Use case**: User preference "I don't want to pay tolls"

#### **departure_time** Parameter
```python
import datetime

# Leave in 2 hours
departure = datetime.datetime.now() + datetime.timedelta(hours=2)

self.client.directions(
    origin,
    destination,
    departure_time=departure
)
```

**Effect**: Uses predicted traffic for that time
- "Leave now" = current traffic
- "Leave at 8 AM tomorrow" = typical Monday 8 AM traffic

#### **waypoints** Parameter
```python
self.client.directions(
    origin="San Jose",
    destination="San Francisco",
    waypoints=["Palo Alto", "Redwood City"]  # Stop along the way
)
```

**Use case**: Carpooling with multiple pickup points!

### Why We Keep It Simple

Our current implementation:
```python
self.client.directions(
    origin,
    destination,
    mode="driving",
    units="metric"
)
```

**We don't use**:
- `avoid` - Could add as user preference later
- `departure_time` - Could add for traffic prediction
- `waypoints` - Definitely needed for multi-stop carpooling!

**Future enhancement** (Section 5: Smart Matching):
```python
# Find route that picks up multiple passengers
waypoints = [passenger1.location, passenger2.location]
route = calculate_route(driver.origin, driver.destination, waypoints=waypoints)
```

---

# Part 4: Async Operations with Sync Libraries

## 16. The Blocking I/O Problem

### Understanding Blocking vs Non-Blocking

This is **crucial** to understand for async Python.

#### **Blocking (Synchronous) Code**

```python
def make_sandwich():
    print("Step 1: Get bread")
    time.sleep(2)  # Wait 2 seconds (BLOCKS)
    print("Step 2: Add peanut butter")
    time.sleep(1)  # Wait 1 second (BLOCKS)
    print("Step 3: Add jelly")
    return "Sandwich ready!"

# If you call this:
result = make_sandwich()  # Takes 3 seconds total
print(result)
```

**What happens**:
- Start Step 1
- **WAIT** 2 seconds (CPU does NOTHING, just waits)
- Step 2
- **WAIT** 1 second
- Step 3
- Total: 3 seconds

**The problem**: While waiting, your program is frozen. Can't do anything else.

#### **Non-Blocking (Asynchronous) Code**

```python
async def make_sandwich():
    print("Step 1: Get bread")
    await asyncio.sleep(2)  # Wait, but DON'T block
    print("Step 2: Add peanut butter")
    await asyncio.sleep(1)
    print("Step 3: Add jelly")
    return "Sandwich ready!"

async def make_coffee():
    print("Boil water")
    await asyncio.sleep(2)  # Wait, but DON'T block
    print("Pour water")
    return "Coffee ready!"

# Run both at same time:
sandwich, coffee = await asyncio.gather(
    make_sandwich(),
    make_coffee()
)
# Total time: 3 seconds (not 5!)
```

**What happens**:
- Start sandwich Step 1
- Start boiling water for coffee
- **BOTH wait simultaneously**
- After 2 seconds: Sandwich Step 2 AND Coffee pour happen
- Total: 3 seconds for BOTH tasks

**The benefit**: While waiting for one thing, do other things.

### Real-World Analogy

**Blocking (Synchronous) Restaurant**:
- Waiter takes order from Table 1
- Stands in kitchen **waiting** for food (5 minutes)
- Brings food to Table 1
- NOW goes to Table 2
- **Result**: Tables 2-10 starving, angry customers

**Non-Blocking (Async) Restaurant**:
- Waiter takes order from Table 1
- Submits to kitchen, immediately goes to Table 2
- Takes order from Table 2, submits to kitchen
- Tables 3, 4, 5...
- When Table 1 food ready, delivers it
- **Result**: All tables served efficiently

### Why This Matters for APIs

**When you call Google Maps API**:
```python
results = client.geocode("San Jose")  # Takes ~500ms
```

**What happens during those 500ms?**
- Send HTTP request to Google → 50ms
- **WAIT** for network → 200ms
- **WAIT** for Google to process → 200ms
- Receive response → 50ms

**350ms of waiting!** During this time:
- **Blocking code**: Server frozen, can't handle other requests
- **Async code**: Server handles 100+ other requests

**For a web server handling 1000 requests/second**, this is the difference between:
- Blocking: Need 100 servers
- Async: Need 5 servers

---

## 17. ThreadPoolExecutor Pattern

### The Problem

**Google Maps Python library is synchronous**:
```python
import googlemaps

client = googlemaps.Client(key="API_KEY")
result = client.geocode("San Jose")  # BLOCKS for ~500ms
```

**Our app is asynchronous**:
```python
async def create_ride(ride_data):
    # This is async code
    result = client.geocode(...)  # ❌ Can't await, it blocks!
```

### The Solution: ThreadPoolExecutor

**Thread Pool** = A group of worker threads ready to do blocking work

```python
from concurrent.futures import ThreadPoolExecutor

# Create pool with 3 worker threads
self._executor = ThreadPoolExecutor(max_workers=3)
```

**Visualization**:
```
Main Async Event Loop:
  ├─ Handle HTTP request 1
  ├─ Handle HTTP request 2
  ├─ Handle HTTP request 3
  └─ ...

Thread Pool (3 workers):
  ├─ Worker Thread 1: [Calling Google Maps API...]
  ├─ Worker Thread 2: [Idle]
  └─ Worker Thread 3: [Idle]
```

### How run_in_executor Works

```python
loop = asyncio.get_event_loop()
results = await loop.run_in_executor(
    self._executor,                          # Which thread pool to use
    lambda: self.client.geocode(address)     # What function to run
)
```

**Step-by-step**:

1. **Main async loop**: "I need to geocode an address, but it's blocking"
2. **run_in_executor**: "Let me hand this to a worker thread"
3. **Worker thread starts**: Runs `self.client.geocode(address)` (BLOCKS the thread)
4. **Main loop continues**: Handles other HTTP requests, database queries, etc.
5. **Worker thread finishes**: "Hey, I got the result!"
6. **run_in_executor**: Passes result back to main loop
7. **Main loop**: `await` completes, continues with result

**The key**: Worker thread is blocked, but **main event loop is NOT blocked**.

### Code Breakdown

```python
# Create executor (done once in __init__)
self._executor = ThreadPoolExecutor(max_workers=3)

# Use it (in each async method)
async def geocode_address(self, address: str):
    loop = asyncio.get_event_loop()  # Get current event loop

    results = await loop.run_in_executor(
        self._executor,                        # Thread pool
        lambda: self.client.geocode(address)   # Blocking function
    )
```

**Line-by-line**:

**`loop = asyncio.get_event_loop()`**
- Gets the current async event loop
- Needed to call `run_in_executor`

**`lambda: self.client.geocode(address)`**
- Creates a function that takes no arguments
- **Why lambda?** `run_in_executor` expects a callable with no args
- The lambda "captures" the `address` variable

**`await loop.run_in_executor(...)`**
- Submits function to thread pool
- **Waits** for result, but doesn't block event loop
- Returns whatever the function returned

### Why max_workers=3?

```python
ThreadPoolExecutor(max_workers=3)
```

**Too few workers** (1):
- Request 1 calls geocode → Worker busy
- Request 2 calls geocode → **WAITS** for worker to be free
- Request 3 calls geocode → **WAITS** in queue
- **Result**: Slow, defeats purpose of async

**Too many workers** (100):
- More memory usage (each thread ~1-2MB)
- More CPU context switching
- Doesn't help if API rate-limited (Google limits concurrent requests)
- **Result**: Wasteful

**Just right** (3-5):
- Handle multiple concurrent requests
- Not too many resources
- **Good rule**: 1-2x number of CPU cores for I/O-bound work

---

## 18. run_in_executor() Explained

### Full Signature

```python
asyncio.run_in_executor(executor, func, *args)
```

**Parameters**:
- `executor`: ThreadPoolExecutor or ProcessPoolExecutor (or None for default)
- `func`: Function to run
- `*args`: Arguments to pass to func

### Different Ways to Use It

#### Method 1: Lambda (What We Use)
```python
result = await loop.run_in_executor(
    self._executor,
    lambda: self.client.geocode(address)
)
```
**Pros**: Concise, can capture variables
**Cons**: Can't pass arguments directly

#### Method 2: Function with Arguments
```python
def geocode_blocking(client, address):
    return client.geocode(address)

result = await loop.run_in_executor(
    self._executor,
    geocode_blocking,
    self.client,
    address
)
```
**Pros**: Clearer for complex functions
**Cons**: More verbose

#### Method 3: functools.partial
```python
from functools import partial

result = await loop.run_in_executor(
    self._executor,
    partial(self.client.geocode, address)
)
```
**Pros**: Functional programming style
**Cons**: Less readable for beginners

### Common Mistake

❌ **WRONG**:
```python
# This won't work - trying to await sync function
result = await self.client.geocode(address)
# Error: object is not awaitable
```

❌ **WRONG**:
```python
# This blocks the event loop - defeats purpose
result = self.client.geocode(address)
# No error, but blocks everything
```

✅ **CORRECT**:
```python
result = await loop.run_in_executor(
    self._executor,
    lambda: self.client.geocode(address)
)
# Works! Doesn't block event loop
```

---

## 19. Why Not Just Use Threads Everywhere?

### Threads vs Async Event Loop

You might ask: "If threads work, why use async at all?"

#### **Threads** (run_in_executor)
**Pros**:
- Can run truly blocking code
- Works with any library
- Parallel execution on multi-core CPU

**Cons**:
- Higher memory usage (~1-2MB per thread)
- CPU context switching overhead
- Limited scalability (OS limits ~1000-5000 threads)
- Thread-safety issues (locks, race conditions)

#### **Async Event Loop**
**Pros**:
- Very lightweight (~1KB per coroutine)
- Can handle 10,000+ concurrent operations
- Single-threaded = no race conditions
- Efficient for I/O-bound work

**Cons**:
- Can't run blocking code directly
- Requires async libraries
- Learning curve (async/await syntax)

### Real Numbers

**Scenario**: Handle 10,000 concurrent HTTP requests

| Approach | Memory Usage | Performance |
|----------|--------------|-------------|
| Sync threads | 10,000 threads × 2MB = **20GB** | Crashes |
| Async | 10,000 coroutines × 1KB = **10MB** | Fast |
| Hybrid (our approach) | Event loop + 3 threads = **~20MB** | Optimal |

### When to Use Each

#### **Use Async** (default choice):
- HTTP requests (with async libraries like httpx)
- Database queries (with async SQLAlchemy)
- Reading files (with aiofiles)
- Waiting for events

#### **Use Threads** (run_in_executor):
- Sync-only libraries (like googlemaps)
- CPU-intensive work (image processing, encryption)
- Calling legacy code
- Can't modify the blocking code

### Our Architecture

```
FastAPI Server (Async)
  ├─ HTTP Handlers (Async)
  │   └─ ride_service methods (Async)
  │       └─ Database queries (Async SQLAlchemy)
  │       └─ MapsClient methods (Async wrapper)
  │           └─ Google Maps calls (Sync in threads)
  └─ Thread Pool (3 workers)
      └─ Blocking Google Maps API calls
```

**Best of both worlds**:
- Most code is async (efficient)
- Google Maps calls use threads (necessary)
- Limited thread pool (controlled resource usage)

---

# Part 5: Caching Strategies

## 20. Why Cache External API Calls?

### The Cost Problem

**Without caching**:
```
Day 1: 100 users search "San Jose State University"
Calls to Google: 100
Cost: 100 × $0.005 = $0.50

Day 30: 3,000 users search "SJSU"
Calls to Google: 3,000
Cost: 3,000 × $0.005 = $15.00

Year 1: ~100,000 searches
Cost: ~$500
```

**With caching**:
```
Day 1: 100 users search "SJSU"
  - First user: Call Google ($0.005)
  - Save result in cache
  - Next 99 users: Use cache ($0)
Cost: $0.005

Day 30: 3,000 users
  - Already cached
Cost: $0

Year 1: ~100,000 searches
Cost: $0.005 (one-time)
Savings: $499.995
```

### Performance Problem

**Without caching**:
```
User searches "SJSU" → Wait 500ms for Google → Show results
```

**With caching**:
```
User searches "SJSU" → Check Redis (5ms) → Show results
```

**100x faster!**

### When to Cache

#### **Always Cache** ✅:
- Geocoding popular addresses (SJSU, SFO, etc.)
- Routes between common locations
- Reverse geocoding (coordinates don't change)

#### **Sometimes Cache** ⚠️:
- Routes with traffic data (cache for 15 minutes)
- User-specific queries (privacy concerns)

#### **Never Cache** ❌:
- Real-time traffic updates
- User location tracking
- Temporary place data

---

## 21. Redis as a Cache Layer

### What is Redis?

**Redis** = **Re**mote **Di**ctionary **S**erver

Think of it as a super-fast, in-memory key-value store:
```python
# Like Python dict, but:
# - Stored in memory (RAM) = very fast
# - Shared across all servers
# - Persisted to disk (optional)
# - Supports expiration (TTL)

cache = {
    "geocode:san_jose_state_university": {"lat": 37.3352, "lng": -121.8811},
    "route:sjsu:sfo": {"distance": 78345, "duration": 3312},
}
```

### Why Redis (vs Other Options)?

#### **Option 1: In-Memory Python Dict**
```python
cache = {}  # Just use a dict
```
**Problems**:
- Lost on server restart
- Not shared across multiple server instances
- No expiration (grows forever)

#### **Option 2: Database (PostgreSQL)**
```python
# Store cache in Postgres table
```
**Problems**:
- Slow (disk I/O)
- Designed for durability, not speed
- Waste of database resources

#### **Option 3: Redis** ✅
```python
# Perfect for caching
```
**Benefits**:
- Very fast (in-memory, ~1ms operations)
- Shared across servers
- Built-in expiration (TTL)
- Rich data types
- Persistence optional

### Redis Architecture in Our App

```
Docker Compose Setup:
┌─────────────────┐
│  ride-service   │
│  (Port 8002)    │
└────────┬────────┘
         │
         ├─ Reads/Writes
         ▼
┌─────────────────┐
│     Redis       │
│   (Port 6379)   │
│  (In Memory)    │
└─────────────────┘
```

**docker-compose.yml**:
```yaml
redis:
  image: redis:7-alpine
  ports: ["6380:6379"]
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

### Basic Redis Operations

#### **SET** - Store value
```python
await redis.set("key", "value")
```

#### **GET** - Retrieve value
```python
value = await redis.get("key")
```

#### **SETEX** - Store with expiration
```python
await redis.setex("key", 3600, "value")  # Expires in 1 hour
```

#### **DELETE** - Remove value
```python
await redis.delete("key")
```

---

## 22. Cache Key Design

### What is a Cache Key?

A **cache key** is a unique identifier for each cached item. Like a filing system:
```
Key: "geocode:san_jose_state_university"
Value: {"lat": 37.3352, "lng": -121.8811}

Key: "route:37.3352,-121.8811:37.6213,-122.3790"
Value: {"distance": 78345, "duration": 3312}
```

### Our Key Generation Strategy

```python
# cache_manager.py

def generate_cache_key(self, operation: str, *args) -> str:
    """
    Generate a consistent cache key.
    Format: "op:arg1:arg2:..."
    Sanitizes spaces to underscores.
    """
    sanitized_args = [str(arg).replace(" ", "_").lower() for arg in args]
    return f"{operation}:{':'.join(sanitized_args)}"
```

### Examples

#### Geocoding Cache Key
```python
# Input
operation = "geocode"
address = "San Jose State University"

# Generated key
cache_manager.generate_cache_key("geocode", address)
# Result: "geocode:san_jose_state_university"

# Why?
# - "San Jose State University" → "san jose state university" (lowercase)
# - Replace spaces with underscores → "san_jose_state_university"
# - Prefix with operation → "geocode:san_jose_state_university"
```

#### Route Cache Key
```python
# Input
operation = "route"
origin = "37.3352,-121.8811"
destination = "37.6213,-122.3790"

# Generated key
cache_manager.generate_cache_key("route", origin, destination)
# Result: "route:37.3352,-121.8811:37.6213,-122.3790"
```

### Why This Format?

#### **Lowercase**
```python
# Without lowercase
"geocode:San_Jose" != "geocode:san_jose" != "geocode:SAN_JOSE"
# Three different keys for same place!

# With lowercase
"geocode:san_jose" == "geocode:san_jose"
# Always same key
```

#### **Replace Spaces**
```python
# Spaces in Redis keys can cause issues
key = "geocode:San Jose State"  # Confusing
key = "geocode:san_jose_state"  # Clean
```

#### **Operation Prefix**
```python
# Organize by type
"geocode:sjsu"       # Geocoding results
"route:sjsu:sfo"     # Route calculations
"user:12345"         # User data (different system)

# Easy to delete all geocode cache:
redis.keys("geocode:*")
```

#### **Colon Separators**
```python
# Standard Redis convention
"operation:arg1:arg2:arg3"

# Makes hierarchy clear
"user:12345:profile"
"user:12345:settings"
```

### Edge Cases Handled

#### Multiple Arguments
```python
generate_cache_key("route", "San Jose", "San Francisco", "driving")
# Result: "route:san_jose:san_francisco:driving"
```

#### Numbers
```python
generate_cache_key("geocode", 37.3352, -121.8811)
# Result: "geocode:37.3352:-121.8811"
# (Converted to strings)
```

#### Special Characters
```python
address = "123 Main St. #456"
generate_cache_key("geocode", address)
# Result: "geocode:123_main_st._#456"
# (Spaces replaced, other chars preserved)
```

---

## 23. TTL (Time To Live) Strategy

### What is TTL?

**TTL** = How long to keep data in cache before it expires

```python
# Set value that expires in 1 hour (3600 seconds)
await redis.setex("key", 3600, "value")

# After 1 hour, Redis automatically deletes it
```

### Why TTL Matters

#### **Without TTL**:
```
Day 1: Cache "route:sjsu:sfo" → {"distance": 78km, "duration": 55min}
Day 365: Still using same cached data
Problem: Traffic patterns changed, new roads built, cache is stale
```

#### **With TTL**:
```
Day 1: Cache with TTL=24 hours
Day 2: Cache expires, new route calculated
Result: Always fresh data within 24 hours
```

### Our TTL Strategy

```python
# cache_manager.py

async def set_cached(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Store a value in cache with TTL (seconds).
    Returns True if successful.
    """
    await self.redis.setex(key, ttl, val_str)
```

**Default: 1 hour (3600 seconds)**

### TTL by Data Type

Different data has different freshness requirements:

#### **Geocoding Results** - Long TTL (24 hours)
```python
ttl = 86400  # 24 hours
```
**Why?** Addresses don't change often
- "San Jose State University" will always be at same coordinates
- Building addresses are stable

#### **Routes WITHOUT Traffic** - Medium TTL (6 hours)
```python
ttl = 21600  # 6 hours
```
**Why?** Roads don't change often, but sometimes they do
- New roads constructed
- Road closures
- Changed traffic patterns

#### **Routes WITH Traffic** - Short TTL (15 minutes)
```python
ttl = 900  # 15 minutes
```
**Why?** Traffic changes constantly
- Rush hour vs off-peak
- Accidents, construction
- Real-time conditions

#### **User Session** - Very Short TTL (30 minutes)
```python
ttl = 1800  # 30 minutes
```
**Why?** Security
- Users should re-login periodically
- Session hijacking risk

### How to Choose TTL

Ask yourself:
1. **How often does this data change?**
   - Rarely (months) → Long TTL (days)
   - Sometimes (weeks) → Medium TTL (hours)
   - Frequently (minutes) → Short TTL (minutes)

2. **What's the cost of stale data?**
   - Low (user sees old address) → Longer TTL
   - High (user charged wrong price) → Shorter TTL

3. **What's the cost of fetching fresh data?**
   - Expensive API call → Longer TTL
   - Cheap database query → Shorter TTL

### Example Calculation

**Geocoding "SJSU"**:
- **How often changes?** Never (building won't move)
- **Cost of stale?** Low (if coordinates off by 0.0001°, doesn't matter)
- **Cost of fresh?** $0.005 per call
- **Decision**: TTL = 24 hours (or even 7 days)

**Route with traffic**:
- **How often changes?** Every minute (traffic updates)
- **Cost of stale?** Medium (user gets wrong ETA)
- **Cost of fresh?** $0.005 per call
- **Decision**: TTL = 15 minutes (balance freshness vs cost)

---

## 24. Cache Invalidation

### The Problem

Sometimes you need to delete cached data **before** it expires:

**Scenario 1**: Road closure
```
Cached route says: 50 minutes
Actual route (due to closure): 90 minutes
User is late and angry!
```

**Scenario 2**: Address correction
```
Geocoded "123 Main St" → Wrong coordinates
Fixed in Google's database
Cached data still wrong for 24 hours
```

**Scenario 3**: User data change
```
User updates profile
Cached profile still shows old data
Confusing!
```

### Cache Invalidation Strategies

#### **Strategy 1: Time-Based (TTL)** - What We Use
```python
# Set TTL when caching
await cache.setex("key", 3600, value)
# Automatically expires after 1 hour
```
**Pros**: Simple, automatic, no extra code
**Cons**: Data might be stale until TTL expires

#### **Strategy 2: Manual Invalidation**
```python
# When data changes, delete cache
async def update_address(address_id, new_data):
    # Update database
    await db.update(address_id, new_data)

    # Delete cached geocoding result
    cache_key = f"geocode:{old_address}"
    await redis.delete(cache_key)
```
**Pros**: Always fresh data
**Cons**: Complex, error-prone (what if you forget to invalidate?)

#### **Strategy 3: Cache Versioning**
```python
# Include version in cache key
CACHE_VERSION = "v2"
key = f"{CACHE_VERSION}:geocode:sjsu"

# To invalidate all cache, bump version
CACHE_VERSION = "v3"  # Old cache automatically ignored
```
**Pros**: Instant global invalidation
**Cons**: Wastes memory (old cache lingers until TTL)

#### **Strategy 4: Event-Based Invalidation**
```python
# Listen for events
@event_listener("address_updated")
async def on_address_updated(address):
    # Invalidate cache
    await redis.delete(f"geocode:{address}")
```
**Pros**: Decoupled, scalable
**Cons**: Complex architecture

### What We Currently Implement

**Currently**: Strategy 1 only (TTL-based)

**Why?**
- Simple to implement
- Good enough for MVP
- Most data is stable (addresses, routes)
- 1-hour staleness is acceptable

### Future Enhancements

When we need better cache control:

#### **Add Manual Invalidation**
```python
# In MapsClient
async def invalidate_geocode(self, address: str):
    """Manually clear geocode cache for an address"""
    key = self.cache_manager.generate_cache_key("geocode", address)
    await self.cache_manager.redis.delete(key)
```

#### **Add Cache Warming**
```python
# Preload popular routes at night
async def warm_cache():
    popular_routes = [
        ("SJSU", "SFO Airport"),
        ("SJSU", "Levi's Stadium"),
        ("SJSU", "Downtown San Jose"),
    ]
    for origin, dest in popular_routes:
        await maps_client.calculate_route(origin, dest)
```

#### **Add Cache Metrics**
```python
# Track hit rate
cache_hits = await redis.get("cache:hits") or 0
cache_misses = await redis.get("cache:misses") or 0
hit_rate = cache_hits / (cache_hits + cache_misses)

if hit_rate < 0.5:
    # Cache not effective, adjust TTL or strategy
```

---

# Part 6: MapsClient Implementation

## 25. File: `shared/utils/maps_client.py` - Architecture

### File Location
```
backend/
  shared/
    utils/
      maps_client.py    ← This file
      cache_manager.py
```

**Why in `shared/`?**
- Both user-service and ride-service might need Maps
- Avoid code duplication
- Shared configuration

### Class Structure

```python
class MapsClient:
    """
    Async wrapper for Google Maps Platform Client.
    Uses ThreadPoolExecutor because the official python client is synchronous.
    """
```

### Class Attributes

```python
def __init__(self, api_key: str, enabled: bool = True):
    self.enabled = enabled           # Can toggle Maps on/off
    self.client = None               # Google Maps client (sync)
    self._executor = None            # Thread pool for async wrapping
```

### Public Methods

```python
async def geocode_address(address: str) -> Optional[Dict[str, Any]]
async def reverse_geocode(lat: float, lng: float) -> Optional[str]
async def calculate_route(origin: str, destination: str) -> Optional[Dict[str, Any]]
```

All methods:
- Are `async` (can be awaited)
- Return `Optional` (might return `None` on error)
- Handle errors gracefully

### Design Patterns Used

#### **1. Wrapper Pattern**
```python
# Wraps googlemaps.Client
self.client = googlemaps.Client(key=api_key)

# Provides async interface
async def geocode_address(self, address):
    return await loop.run_in_executor(...)
```

#### **2. Circuit Breaker Pattern** (Simplified)
```python
if not self.enabled or not self.client:
    return None  # Fail fast, don't call Google
```

#### **3. Error Handling**
```python
try:
    # Call Google
except Exception as e:
    logger.error(...)
    return None  # Never crash, return None
```

---

## 26. Initialization and Configuration

### The __init__ Method

```python
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
```

### Line-by-Line Breakdown

**Line 14**: `def __init__(self, api_key: str, enabled: bool = True)`
- Takes API key (required)
- `enabled` flag (optional, defaults to `True`)

**Line 15**: `self.enabled = enabled`
- Store enabled state
- Can be `False` to disable Maps entirely

**Line 16**: `self.client = None`
- Initialize client as `None`
- Will be set if initialization succeeds

**Lines 17-22**: Try to initialize Google client
```python
if enabled and api_key:  # Only if both enabled AND key provided
    try:
        self.client = googlemaps.Client(key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Google Maps client: {e}")
        self.enabled = False  # Disable if init fails
```

**Possible exceptions**:
- Invalid API key format
- Network error connecting to Google
- Library not installed

**Lines 23-26**: Handle missing API key
```python
else:
    self.enabled = False
    if not api_key:
        logger.warning("Google Maps API Key missing. Maps features disabled.")
```

**Why warning, not error?**
- It's OK to run without Maps (for development)
- App still works, just requires manual coordinates

**Line 28**: Create thread pool
```python
self._executor = ThreadPoolExecutor(max_workers=3)
```
- Always create executor (even if disabled)
- Prevents errors if state changes later

### Usage in Ride Service

```python
# ride_service.py

class RideService:
    def __init__(self):
        self.maps_client = MapsClient(
            api_key=settings.GOOGLE_MAPS_API_KEY,
            enabled=settings.GOOGLE_MAPS_ENABLED
        )
```

**Configuration**:
```python
# .env file
GOOGLE_MAPS_API_KEY=AIzaSy...
GOOGLE_MAPS_ENABLED=True

# For development without API key
GOOGLE_MAPS_API_KEY=
GOOGLE_MAPS_ENABLED=False
```

---

## 27-29. Geocode, Reverse Geocode, Calculate Route Methods

*(Covered in detail in Parts 2-3)*

**Summary**:
- All use same pattern: Check enabled → run_in_executor → handle errors
- Return `None` on any error (graceful degradation)
- Log errors for debugging

---

## 30. Error Handling and Logging

### Error Handling Philosophy

**Never crash, always degrade gracefully**:
```python
try:
    result = await maps_client.geocode_address("San Jose")
    if result:
        # Use geocoded coordinates
    else:
        # Ask user for manual coordinates
except Exception:
    # This should never happen (we catch inside methods)
    # But even if it does, handle it
```

### Logging Levels

```python
import logging
logger = logging.getLogger(__name__)
```

#### **logger.error()** - Something went wrong
```python
logger.error(f"Geocode error for '{address}': {e}")
```
**When**: API call failed, invalid response, network error
**Action**: Investigate, might need to fix code or contact Google

#### **logger.warning()** - Not ideal, but OK
```python
logger.warning("Google Maps API Key missing. Maps features disabled.")
```
**When**: Missing config, degraded functionality
**Action**: Check configuration, but app still works

#### **logger.info()** - Normal operation
```python
logger.info(f"Geocoded '{address}' to {lat}, {lng}")
```
**When**: Successful operations, state changes
**Action**: None, just for monitoring

#### **logger.debug()** - Detailed info
```python
logger.debug(f"Cache hit for key: {cache_key}")
```
**When**: Debugging, development
**Action**: Only shown if LOG_LEVEL=DEBUG

### What Gets Logged

```python
# Successful geocode
INFO:shared.utils.maps_client:Geocoded 'SJSU' to 37.3352, -121.8811

# Failed geocode
ERROR:shared.utils.maps_client:Geocode error for 'invalid address xyz': API error

# Missing API key
WARNING:shared.utils.maps_client:Google Maps API Key missing. Maps features disabled.

# Route calculation
INFO:shared.utils.maps_client:Calculated route: 78.3 km, 55 mins
```

### Production Logging

In production, logs go to:
- **Console** (captured by Docker)
- **Log files** (if configured)
- **Log aggregation service** (like CloudWatch, Datadog)

```bash
# View logs in Docker
docker logs sjsu-ride-service

# Follow logs in real-time
docker logs -f sjsu-ride-service

# Search logs
docker logs sjsu-ride-service | grep "ERROR"
```

---

# Part 7: CacheManager Implementation

## 31. File: `shared/utils/cache_manager.py` - Architecture

### Class Overview

```python
class CacheManager:
    """
    Manages caching operations using Redis.
    Structure: Key-Value pairs with TTL.
    """
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
```

**Why separate class?**
- **Separation of concerns**: MapsClient handles Maps, CacheManager handles caching
- **Reusability**: Can cache other data (user profiles, search results)
- **Testability**: Can mock Redis client easily

### Methods

```python
async def get_cached(key: str) -> Optional[Dict[str, Any]]
async def set_cached(key: str, value: Dict[str, Any], ttl: int = 3600) -> bool
def generate_cache_key(operation: str, *args) -> str
```

---

## 32. Get Cached Method

```python
async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a value from cache.
    Returns deserialized JSON dict or None if miss.
    """
    try:
        val = await self.redis.get(key)
        if val:
            return json.loads(val)
        return None
    except Exception as e:
        logger.error(f"Cache GET error for {key}: {e}")
        return None
```

### How It Works

**Step 1**: Ask Redis for value
```python
val = await self.redis.get(key)
# Returns: bytes or None
```

**Step 2**: If found, deserialize JSON
```python
if val:
    return json.loads(val)
# Converts: b'{"lat": 37.3352, "lng": -121.8811}'
# To: {"lat": 37.3352, "lng": -121.8811}
```

**Step 3**: If not found or error, return None
```python
return None
```

### Cache Hit vs Miss

#### **Cache Hit** (data found):
```python
key = "geocode:sjsu"
result = await cache_manager.get_cached(key)
# result = {"lat": 37.3352, "lng": -121.8811}
```

#### **Cache Miss** (data not found):
```python
key = "geocode:some_new_address"
result = await cache_manager.get_cached(key)
# result = None
```

### Usage Example

```python
# Try cache first
cache_key = cache_manager.generate_cache_key("geocode", address)
cached = await cache_manager.get_cached(cache_key)

if cached:
    # Cache hit! Use it
    return cached
else:
    # Cache miss, call Google
    result = await call_google_maps_api(address)
    # Save to cache for next time
    await cache_manager.set_cached(cache_key, result)
    return result
```

---

## 33. Set Cached Method

```python
async def set_cached(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Store a value in cache with TTL (seconds).
    Returns True if successful.
    """
    try:
        # Serialize to JSON
        val_str = json.dumps(value)
        await self.redis.setex(key, ttl, val_str)
        return True
    except Exception as e:
        logger.error(f"Cache SET error for {key}: {e}")
        return False
```

### How It Works

**Step 1**: Serialize dict to JSON string
```python
value = {"lat": 37.3352, "lng": -121.8811}
val_str = json.dumps(value)
# Result: '{"lat": 37.3352, "lng": -121.8811}'
```

**Why serialize?**
- Redis stores strings, not Python objects
- JSON is standard, language-agnostic format

**Step 2**: Store in Redis with TTL
```python
await self.redis.setex(key, ttl, val_str)
```
- `setex` = SET with EXpiration
- `key` = Cache key
- `ttl` = Seconds until expiration
- `val_str` = JSON string to store

**Step 3**: Return success status
```python
return True  # Successful
return False # Error occurred
```

### Parameters

#### **ttl (Time To Live)**
Default: 3600 seconds (1 hour)

```python
# 1 hour
await cache_manager.set_cached(key, value, ttl=3600)

# 24 hours
await cache_manager.set_cached(key, value, ttl=86400)

# 5 minutes
await cache_manager.set_cached(key, value, ttl=300)
```

---

## 34-35. Cache Key Generation and JSON Serialization

*(Covered in Part 5, Topics 22 and 33)*

---

# Part 8: Integration with Ride Service

## 36. How Ride Service Uses MapsClient

### Initialization

```python
# ride_service.py

class RideService:
    def __init__(self):
        self.maps_client = MapsClient(
            api_key=settings.GOOGLE_MAPS_API_KEY,
            enabled=settings.GOOGLE_MAPS_ENABLED
        )
```

**When created**: Once, when ride-service starts

**Configuration from**:
```python
# ride-service/app/core/config.py
class Settings(BaseSettings):
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_MAPS_ENABLED: bool = True
```

**Values from**:
```bash
# .env or environment variables
GOOGLE_MAPS_API_KEY=AIzaSy...
GOOGLE_MAPS_ENABLED=True
```

---

## 37. Auto-Geocoding in Ride Creation

### The Flow

**User submits ride**:
```json
{
  "origin": {
    "address": "San Jose State University",
    "lat": null,
    "lng": null
  },
  "destination": {
    "address": "SFO Airport",
    "lat": null,
    "lng": null
  }
}
```

**Ride service auto-geocodes**:

```python
# ride_service.py

async def create_ride(self, ride_data: RideCreate, driver_id: UUID, db: AsyncSession):
    # 1. Verify Driver
    driver = await user_client.get_user(driver_id)

    # 2. Geocode Origin if needed
    if (ride_data.origin.lat is None or ride_data.origin.lng is None):
        if self.maps_client.enabled:
            geo_res = await self.maps_client.geocode_address(ride_data.origin.address)
            if geo_res:
                ride_data.origin.lat = geo_res['lat']
                ride_data.origin.lng = geo_res['lng']
            else:
                raise ValueError(f"Could not geocode origin: {ride_data.origin.address}")
        else:
            raise ValueError("Coordinates required for origin when Maps disabled")

    # 3. Geocode Destination (same logic)
    if (ride_data.destination.lat is None or ride_data.destination.lng is None):
        # ... same as origin

    # 4. Create Ride with coordinates
    ride = Ride(
        origin_lat=ride_data.origin.lat,
        origin_lng=ride_data.origin.lng,
        ...
    )
```

### Step-by-Step Breakdown

**Step 1**: Check if coordinates missing
```python
if (ride_data.origin.lat is None or ride_data.origin.lng is None):
```

**Step 2**: Check if Maps enabled
```python
if self.maps_client.enabled:
```

**Step 3**: Call geocoding
```python
geo_res = await self.maps_client.geocode_address(ride_data.origin.address)
```

**Step 4**: If successful, update ride_data
```python
if geo_res:
    ride_data.origin.lat = geo_res['lat']
    ride_data.origin.lng = geo_res['lng']
```

**Step 5**: If failed, raise error
```python
else:
    raise ValueError(f"Could not geocode origin: {ride_data.origin.address}")
```

### Three Possible Outcomes

#### **Outcome 1: User provides coordinates** ✅
```json
{
  "origin": {
    "address": "SJSU",
    "lat": 37.3352,
    "lng": -121.8811
  }
}
```
**Result**: Skip geocoding, use provided coordinates

#### **Outcome 2: Auto-geocode succeeds** ✅
```json
{
  "origin": {
    "address": "San Jose State University",
    "lat": null,
    "lng": null
  }
}
```
**Result**: Geocode → Update lat/lng → Create ride

#### **Outcome 3: Auto-geocode fails** ❌
```json
{
  "origin": {
    "address": "asdf invalid address",
    "lat": null,
    "lng": null
  }
}
```
**Result**: Raise ValueError → HTTP 400 error → User sees error message

---

## 38. Route Preview Endpoint

### The Endpoint

```python
# rides.py

@router.get("/{ride_id}/preview-route")
async def preview_route(
    ride_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get route preview (distance, duration, polyline) for a ride.
    """
    try:
        route = await ride_service.preview_route(ride_id, db)
        if not route:
            raise HTTPException(status_code=404, detail="Ride not found or route calculation failed")
        return route
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### The Service Method

```python
# ride_service.py

async def preview_route(self, ride_id: UUID, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Get route preview for a ride"""
    ride = await self.get_ride(ride_id, db)
    if not ride:
        return None

    origin = f"{ride.origin_lat},{ride.origin_lng}"
    destination = f"{ride.destination_lat},{ride.destination_lng}"

    return await self.maps_client.calculate_route(origin, destination)
```

### Example Usage

**Request**:
```http
GET /api/v1/rides/123e4567-e89b-12d3-a456-426614174000/preview-route
```

**Response**:
```json
{
  "distance_value": 78345,
  "distance_text": "78.3 km",
  "duration_value": 3312,
  "duration_text": "55 mins",
  "start_address": "San Jose State University, San Jose, CA",
  "end_address": "San Francisco International Airport, San Francisco, CA",
  "polyline": "m~feFbx~Uh@y@BIrADwC..."
}
```

**Frontend can use this to**:
- Display distance and duration to user
- Draw route on map using polyline
- Calculate estimated price based on distance
- Show start/end addresses

---

## 39. Fallback When Maps Disabled

### Graceful Degradation

When `GOOGLE_MAPS_ENABLED=False`:

```python
# MapsClient returns None for all methods
maps_client.enabled = False

result = await maps_client.geocode_address("SJSU")
# result = None
```

### How Ride Service Handles It

#### **Option 1: Require Manual Coordinates**
```python
if (ride_data.origin.lat is None or ride_data.origin.lng is None):
    if self.maps_client.enabled:
        # Try to geocode
    else:
        raise ValueError("Coordinates required for origin when Maps disabled")
```

**User experience**:
```json
// User must provide coordinates
{
  "origin": {
    "address": "SJSU",
    "lat": 37.3352,  // Required when Maps disabled
    "lng": -121.8811
  }
}
```

#### **Option 2: No Route Preview**
```python
route = await ride_service.preview_route(ride_id, db)
# route = None

# Endpoint returns 404
raise HTTPException(status_code=404, detail="Route calculation unavailable")
```

**User experience**:
- Can create rides (with manual coordinates)
- Can search rides
- Can book rides
- **Cannot** see route preview or distance/duration estimates

### Why This Design?

**Allows development without API key**:
```bash
# Local development
GOOGLE_MAPS_ENABLED=False

# User provides all coordinates manually
# App works fine for testing other features
```

**Allows cost control**:
```bash
# If approaching quota limit
GOOGLE_MAPS_ENABLED=False

# App degrades gracefully
# Users can still book rides, just less convenient
```

**Allows redundancy**:
```bash
# If Google Maps has outage
# Automatically falls back to manual coordinates
# App doesn't crash
```

---

# Part 9: Testing External APIs

## 40. Mocking External Services

### Why Mock External APIs?

**Problems with calling real APIs in tests**:
1. **Slow**: Each test waits ~500ms for API response
2. **Expensive**: 1000 tests = 1000 API calls = $5
3. **Flaky**: Tests fail if network down or API rate limited
4. **Not isolated**: Testing our code + Google's code together

**Solution: Mock the external service**

### What is Mocking?

**Mocking** = Replace real object with fake one that returns predefined responses

```python
# Real code
result = await google_maps_client.geocode("SJSU")
# Calls Google, takes 500ms, costs $0.005

# Mocked code
mock_client.geocode = Mock(return_value={"lat": 37.3352, "lng": -121.8811})
result = mock_client.geocode("SJSU")
# Returns instantly, free, predictable
```

### Mocking Levels

#### **Level 1: Mock the HTTP request**
```python
@patch('httpx.AsyncClient.get')
async def test_geocode(mock_get):
    mock_get.return_value = MockResponse(...)
```
**Tests**: HTTP layer

#### **Level 2: Mock the library**
```python
@patch('googlemaps.Client')
async def test_geocode(mock_client):
    mock_client.geocode.return_value = [...]
```
**Tests**: Our wrapper around library

#### **Level 3: Mock our class** (What we do)
```python
ride_service.maps_client.geocode_address = AsyncMock(
    return_value={"lat": 37.3352, "lng": -121.8811}
)
```
**Tests**: Business logic using MapsClient

---

## 41. Test File: `test_maps.py` Walkthrough

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ride_service import RideService
from shared.utils.maps_client import MapsClient

# Mock data
params = {...}

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_user_client():
    with patch("app.services.ride_service.user_client") as mock:
        mock.get_user = AsyncMock(return_value={...})
        yield mock

@pytest.fixture
def ride_service():
    return RideService()

@pytest.mark.asyncio
async def test_create_ride_auto_geocode(ride_service, mock_db, mock_user_client):
    # Test implementation
```

### Key Concepts

#### **@pytest.fixture**
Creates reusable test components:
```python
@pytest.fixture
def mock_db():
    return AsyncMock()  # Fake database

# Each test gets a fresh mock_db
def test_one(mock_db):
    # Gets new AsyncMock()

def test_two(mock_db):
    # Gets different AsyncMock()
```

#### **AsyncMock**
Mock for async functions:
```python
mock_func = AsyncMock(return_value=42)
result = await mock_func()  # result = 42
```

#### **@pytest.mark.asyncio**
Allows async test functions:
```python
@pytest.mark.asyncio
async def test_something():
    result = await async_function()
```

---

## 42. Unit Testing with AsyncMock

### Test 1: Auto-Geocoding Success

```python
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

    # Create ride
    ride = await ride_service.create_ride(ride_in, driver_id, mock_db)

    # Verify geocode was called
    ride_service.maps_client.geocode_address.assert_called_with("San Jose State University")

    # Verify coords were set on the model
    assert ride.origin_lat == 37.3352
    assert ride.origin_lng == -121.8811
```

### Breaking Down the Test

**Setup**: Mock the geocode method
```python
ride_service.maps_client.geocode_address = AsyncMock(return_value={
    "lat": 37.3352, "lng": -121.8811, "formatted_address": "SJSU"
})
```
**What this does**:
- Replace real `geocode_address` with fake one
- Fake one returns predefined coordinates
- No actual Google API call

**Action**: Create ride with missing coordinates
```python
ride_in = RideCreate(**params)  # params has address but no coords
ride = await ride_service.create_ride(ride_in, driver_id, mock_db)
```

**Assertions**: Verify behavior
```python
# Was geocode called with correct address?
ride_service.maps_client.geocode_address.assert_called_with("San Jose State University")

# Were coordinates set correctly?
assert ride.origin_lat == 37.3352
assert ride.origin_lng == -121.8811
```

---

## 43. Testing Error Scenarios

### Test 2: Maps Disabled

```python
@pytest.mark.asyncio
async def test_create_ride_maps_disabled_fail(ride_service, mock_db, mock_user_client):
    """Test failure when coords missing and Maps disabled"""

    ride_service.maps_client.enabled = False

    ride_in = RideCreate(**params)
    driver_id = uuid4()

    with pytest.raises(ValueError, match="Coordinates required"):
        await ride_service.create_ride(ride_in, driver_id, mock_db)
```

### Understanding pytest.raises

```python
with pytest.raises(ValueError, match="Coordinates required"):
    # Code that should raise ValueError
```

**What this does**:
- Expects the code inside to raise `ValueError`
- Error message should contain "Coordinates required"
- If no error → Test fails
- If wrong error → Test fails
- If correct error → Test passes

### Test 3: Route Preview

```python
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
```

### Why MagicMock vs AsyncMock?

**MagicMock**: For regular objects/synchronous functions
```python
mock_ride = MagicMock()
mock_ride.origin_lat = 37.3352  # Set attributes
```

**AsyncMock**: For async functions
```python
ride_service.get_ride = AsyncMock(return_value=mock_ride)
result = await ride_service.get_ride(ride_id, db)  # Can await
```

---

# Part 10: Real-World Scenarios

## 44. Cost Optimization Techniques

### Current Implementation

**What we do**:
1. ✅ Use coordinates format for routes (saves geocoding calls)
2. ✅ Have enable/disable toggle
3. ✅ Cache manager infrastructure in place

**What we DON'T do yet**:
1. ❌ Actually use cache in MapsClient
2. ❌ Batch geocoding requests
3. ❌ Client-side geocoding for some features

### Cost Analysis

**Without optimization**:
```
Monthly usage:
- 10,000 ride creations (2 geocodes each) = 20,000 geocode calls
- 10,000 route previews = 10,000 directions calls
Total calls: 30,000
Cost: 30,000 × $0.005 = $150/month
Annual: $1,800
```

**With caching (50% hit rate)**:
```
Geocoding:
- 20,000 calls → 10,000 cache hits + 10,000 API calls
- Cost: $50

Directions:
- 10,000 calls → 5,000 cache hits + 5,000 API calls
- Cost: $25

Total: $75/month
Annual: $900 (save $900/year)
```

**With caching (80% hit rate)**:
```
Total: $30/month
Annual: $360 (save $1,440/year)
```

### How to Improve Cache Hit Rate

#### **1. Normalize Addresses**
```python
# Before caching, standardize
address = address.lower().strip()
address = re.sub(r'\s+', ' ', address)  # Multiple spaces → single space
address = address.replace('avenue', 'ave')
address = address.replace('street', 'st')

# "San Jose State University" == "san jose state university"
# "123  Main   St" == "123 main st"
```

#### **2. Preload Popular Locations**
```python
# On server startup, geocode common addresses
POPULAR_LOCATIONS = [
    "San Jose State University",
    "San Francisco International Airport",
    "Levi's Stadium",
    "Great America"
]

for loc in POPULAR_LOCATIONS:
    await maps_client.geocode_address(loc)  # Populates cache
```

#### **3. Longer TTL for Stable Data**
```python
# Geocoding: 7 days (addresses don't move)
await cache.set_cached(key, result, ttl=604800)

# Routes: 6 hours (roads rarely change)
await cache.set_cached(key, result, ttl=21600)
```

#### **4. Analytics-Driven Caching**
```python
# Track most searched locations
popular_routes = await analytics.get_popular_routes(limit=100)

# Warm cache for top routes
for origin, dest in popular_routes:
    await maps_client.calculate_route(origin, dest)
```

---

## 45. Handling API Rate Limits

### Google Maps Quotas

**Default quotas** (can request increase):
- Geocoding: 50 requests/second
- Directions: 50 requests/second
- Daily limit: Based on billing

### What Happens When Rate Limited

**Response from Google**:
```json
{
  "status": "OVER_QUERY_LIMIT",
  "error_message": "You have exceeded your rate-limit for this API."
}
```

**Our current handling**:
```python
except Exception as e:
    logger.error(f"Geocode error: {e}")
    return None  # User sees error
```

**Not ideal!** User can't create ride.

### Better Rate Limit Handling

#### **Strategy 1: Exponential Backoff**
```python
async def geocode_with_retry(self, address: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.geocode_address(address)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)
            else:
                raise
```

#### **Strategy 2: Request Queue**
```python
# Limit concurrent requests to Google
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent

async def geocode_address(self, address):
    async with semaphore:  # Wait if 10 already running
        return await self._geocode_internal(address)
```

#### **Strategy 3: Circuit Breaker**
```python
class CircuitBreaker:
    def __init__(self):
        self.failures = 0
        self.threshold = 5
        self.open = False

    async def call(self, func, *args):
        if self.open:
            raise Exception("Circuit breaker open, service unavailable")

        try:
            result = await func(*args)
            self.failures = 0  # Reset on success
            return result
        except RateLimitError:
            self.failures += 1
            if self.failures >= self.threshold:
                self.open = True  # Stop trying
            raise
```

**How it works**:
- Track failures
- After 5 failures in a row, "open" circuit
- Stop making requests (fail fast)
- Periodically try again (close circuit if succeeds)

---

## 46. Graceful Degradation

### Levels of Degradation

#### **Level 1: Full Functionality**
```
✅ Google Maps enabled
✅ Auto-geocoding works
✅ Route preview works
✅ Distance/duration estimates
```

#### **Level 2: Partial Degradation**
```
⚠️ Google Maps slow/rate limited
✅ Cached geocodes work
✅ Recent routes work
❌ New addresses fail
❌ New routes fail
```

**User experience**: Some features work, some don't

#### **Level 3: Graceful Fallback**
```
❌ Google Maps completely down
✅ Accept manual coordinates
✅ Search/book rides still work
❌ No auto-geocoding
❌ No route preview
```

**User experience**: Core features work, convenience features don't

#### **Level 4: Complete Failure**
```
❌ Google Maps down
❌ No fallback
❌ Can't create rides at all
```

**User experience**: App broken

**Our implementation**: Level 3 (Graceful Fallback) ✅

### Implementation

```python
# In create_ride
if coordinates_missing:
    if maps_enabled:
        try:
            # Try to geocode
        except:
            # Ask user for coordinates
    else:
        # Ask user for coordinates

# In preview_route
if maps_enabled:
    # Show route
else:
    # Show "Route preview unavailable"
```

---

## 47. Monitoring and Logging

### What to Monitor

#### **1. API Call Volume**
```python
# Increment counter for each call type
await redis.incr("metrics:geocode:count")
await redis.incr("metrics:directions:count")

# Daily report
geocode_count = await redis.get("metrics:geocode:count")
logger.info(f"Geocode calls today: {geocode_count}")
```

#### **2. Cache Hit Rate**
```python
# Track hits/misses
if cached_result:
    await redis.incr("cache:hits")
else:
    await redis.incr("cache:misses")

# Calculate rate
hits = int(await redis.get("cache:hits") or 0)
misses = int(await redis.get("cache:misses") or 0)
hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

logger.info(f"Cache hit rate: {hit_rate:.2%}")
```

#### **3. Error Rates**
```python
# Track errors
try:
    result = await geocode_address(address)
    await redis.incr("metrics:geocode:success")
except:
    await redis.incr("metrics:geocode:error")
    raise

# Alert if error rate > 5%
error_rate = errors / (successes + errors)
if error_rate > 0.05:
    send_alert("High geocoding error rate!")
```

#### **4. API Latency**
```python
import time

start = time.time()
result = await geocode_address(address)
duration = time.time() - start

logger.info(f"Geocode latency: {duration:.3f}s")

# Track percentiles
await redis.zadd("latency:geocode", {str(time.time()): duration})
```

### Log Examples

**Successful operation**:
```
INFO:2024-01-15 10:30:45:Geocoded 'SJSU' to 37.3352,-121.8811 in 0.234s
```

**Cache hit**:
```
DEBUG:2024-01-15 10:30:46:Cache hit for geocode:sjsu
```

**Rate limit warning**:
```
WARNING:2024-01-15 10:31:00:Approaching rate limit, 45/50 requests used
```

**Error**:
```
ERROR:2024-01-15 10:31:15:Geocode failed for 'invalid address': API error
```

### Alerting

**Set up alerts for**:
1. Error rate > 5%
2. API latency > 2 seconds
3. Cache hit rate < 50%
4. Approaching daily quota (80%)
5. Any OVER_QUERY_LIMIT errors

---

## 48. Production Best Practices

### 1. API Key Security

#### **Do's** ✅:
- Store in environment variables
- Use separate keys for dev/staging/prod
- Restrict by IP address
- Restrict to only needed APIs
- Rotate keys periodically

#### **Don'ts** ❌:
- Commit to git
- Hardcode in source
- Use same key for all environments
- Share keys in Slack/email
- Use unrestricted keys

### 2. Error Handling

```python
# ❌ BAD
result = await geocode(address)  # Crashes if fails

# ✅ GOOD
try:
    result = await geocode(address)
except APIError as e:
    logger.error(f"API error: {e}")
    return None
except NetworkError as e:
    logger.error(f"Network error: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return None
```

### 3. Configuration

```python
# ✅ GOOD: Configurable, with sensible defaults
class Settings:
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_MAPS_ENABLED: bool = True
    GEOCODE_CACHE_TTL: int = 86400  # 24 hours
    ROUTE_CACHE_TTL: int = 21600    # 6 hours
    MAPS_TIMEOUT: int = 10          # seconds
    MAPS_MAX_RETRIES: int = 3
```

### 4. Caching

```python
# Cache key versioning for easy invalidation
CACHE_VERSION = "v1"
key = f"{CACHE_VERSION}:geocode:{address}"

# Appropriate TTLs
GEOCODE_TTL = 86400    # 24h - addresses rarely change
ROUTE_TTL = 21600      # 6h - roads occasionally change
TRAFFIC_TTL = 900      # 15min - traffic changes frequently
```

### 5. Testing

```python
# Test all scenarios
- ✅ Successful API calls
- ✅ Failed API calls
- ✅ Rate limiting
- ✅ Timeouts
- ✅ Invalid input
- ✅ Maps disabled
- ✅ Cache hits/misses
```

### 6. Monitoring

**Track**:
- API call volume
- Cost (estimate)
- Error rates
- Cache hit rates
- Latency percentiles (p50, p95, p99)

**Alert on**:
- High error rate
- High latency
- Approaching quota
- Low cache hit rate

### 7. Documentation

Document:
- How to get API key
- How to configure
- Error codes and meanings
- Cache strategy
- Cost estimates
- Troubleshooting guide

---

## Summary

Congratulations! You've completed the Google Maps Integration learning guide.

### What You Learned

**Part 1-3: Google Maps APIs**
- Geocoding (address ↔ coordinates)
- Directions (route calculation)
- API keys, quotas, pricing
- Response structures

**Part 4: Async Operations**
- Blocking vs non-blocking I/O
- ThreadPoolExecutor pattern
- `run_in_executor()` for sync libraries
- When to use threads vs async

**Part 5: Caching**
- Why cache external APIs
- Redis as cache layer
- Cache key design
- TTL strategies
- Cache invalidation

**Part 6-7: Implementation**
- MapsClient wrapper class
- CacheManager class
- Error handling
- Logging

**Part 8: Integration**
- Auto-geocoding in ride creation
- Route preview endpoint
- Graceful fallback when Maps disabled

**Part 9: Testing**
- Mocking external services
- AsyncMock vs MagicMock
- Testing error scenarios
- Test file walkthrough

**Part 10: Real-World**
- Cost optimization (save $900+/year)
- Rate limit handling
- Graceful degradation
- Monitoring and alerting
- Production best practices

### Next Steps

Now that you understand Google Maps integration, you're ready for:
- **Section 5**: Smart matching algorithm (using geospatial data)
- **Section 6**: Booking service (reserving seats on rides)
- **Section 7**: Notification service (alerting users)

### Key Takeaways

1. **External APIs are expensive** - Cache aggressively
2. **External APIs can fail** - Handle errors gracefully
3. **Sync libraries in async code** - Use ThreadPoolExecutor
4. **Security matters** - Never commit API keys
5. **Monitor everything** - You can't fix what you don't measure

You now have a solid foundation in integrating external services into microservices architecture!
