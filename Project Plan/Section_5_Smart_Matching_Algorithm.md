# SJSU RideShare Development Guide
## Section 5: Smart Ride Matching Algorithm

**Version:** 1.0  
**Duration:** Week 5  
**Focus:** Intelligent algorithm to match passengers with optimal rides

---

# SECTION 5: Smart Ride Matching Algorithm

## Learning Objectives
- Algorithm design and scoring systems
- Multi-criteria decision making
- Geospatial route compatibility
- Performance optimization techniques
- Caching for expensive operations

## Technologies
- Python algorithms
- Geospatial mathematics
- Redis caching
- Google Maps Directions API
- Scoring and ranking systems

## Prerequisites
- Sections 1-4 completed ✅
- Google Maps integration working
- Understanding of algorithms
- Basic linear algebra (vectors, angles)

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Smart Ride Matching Algorithm

CONTEXT:
Sections 1-4 completed. Users can post and search rides.
Now implementing intelligent matching algorithm that scores rides based on:
- Route compatibility
- Time match
- Price
- Driver rating
- Preference alignment

GOAL:
Create smart matching algorithm that finds best ride matches for passengers
considering routes, detours, preferences, and rankings.

DETAILED REQUIREMENTS:

1. MATCHING SERVICE (ride-service/app/services/matching_service.py):

   Core function signature:
   ```python
   async def find_matching_rides(
       passenger_origin: dict,  # {lat, lng, address}
       passenger_destination: dict,
       departure_time_range: tuple,  # (start_datetime, end_datetime)
       min_seats: int = 1,
       max_price: float = None,
       preferences: dict = None,
       passenger_rating: float = 5.0,
       db: AsyncSession
   ) -> List[dict]:
   ```

   Algorithm Steps:
   
   A. FILTER RIDES (Database Level):
      - Status = "active"
      - Available seats >= min_seats
      - Departure time within range
      - Price <= max_price (if specified)
      - Departure time > now + 1 hour
   
   B. CALCULATE ROUTE COMPATIBILITY:
      For each filtered ride:
      
      1. Pickup Feasibility:
         - Distance from driver origin to passenger origin
         - Should be < 5 km (configurable)
      
      2. Dropoff Feasibility:
         - Distance from driver destination to passenger destination  
         - Should be < 5 km
      
      3. Calculate Detour:
         - Original route: Driver A → B
         - With passenger: Driver A → Passenger Origin → Passenger Dest → B
         - Use Google Maps Directions API (cached)
         - Detour = new_distance - original_distance
         - Maximum acceptable: 10 km or 15 minutes
      
      4. Direction Alignment:
         - Calculate bearing from driver origin to destination
         - Calculate bearing from driver origin to passenger destination
         - Angle difference should be < 45 degrees
         - Use calculate_bearing() from geo utils
   
   C. CALCULATE COMPATIBILITY SCORE (0-100):
      
      Component breakdown:
      
      1. Route Score (40 points max):
         - 0 km detour: 40 points
         - 0-5 km detour: 35 points
         - 5-10 km detour: 30 points  
         - 10-15 km detour: 20 points
         - > 15 km: 0 points (filtered out)
      
      2. Time Score (20 points max):
         - Exact time match: 20 points
         - Within 15 min: 15 points
         - Within 30 min: 10 points
         - Within 1 hour: 5 points
         - > 1 hour: 0 points
      
      3. Price Score (15 points max):
         - Free: 15 points
         - < $5: 12 points
         - $5-$10: 8 points
         - $10-$20: 5 points
         - > $20: 2 points
      
      4. Driver Rating Score (15 points max):
         - 5.0 rating: 15 points
         - 4.5-4.9: 12 points
         - 4.0-4.4: 8 points
         - 3.5-3.9: 5 points
         - < 3.5: 2 points
      
      5. Preference Match Score (10 points max):
         - All preferences match: 10 points
         - Partial match: 5 points
         - No preferences specified: 7 points (neutral)
         - Conflicting preferences: 0 points
      
      Formula:
      ```python
      total_score = (
          route_score + 
          time_score + 
          price_score + 
          rating_score + 
          preference_score
      )
      ```
   
   D. RANK AND RETURN:
      - Sort by compatibility score (highest first)
      - Return top 20 matches
      - Include score breakdown for transparency
      - Include estimated pickup/dropoff times
      - Include detour information

2. MATCHING UTILITIES (ride-service/app/utils/matching_utils.py):

   Functions to implement:
   
   A. calculate_route_detour(driver_origin, driver_dest, pass_origin, pass_dest) -> dict:
      - Use Google Maps Directions API
      - Calculate original route distance/time
      - Calculate route with passenger waypoints
      - Return: {"distance_km": x, "time_minutes": y}
      - Cache for 1 hour
   
   B. check_direction_alignment(origin, destination, passenger_dest) -> bool:
      - Calculate bearing from origin to destination
      - Calculate bearing from origin to passenger destination
      - Return True if angle difference < 45 degrees
   
   C. match_preferences(ride_prefs, passenger_prefs) -> float:
      - Compare each preference
      - Return match percentage (0-1)
      - Example:
        * ride: {music: true, ac: true, stops: false}
        * passenger: {music: true, ac: true}
        * Match: 1.0 (all passenger prefs matched)
   
   D. calculate_time_difference(ride_time, preferred_time) -> int:
      - Return absolute difference in minutes
      - Used for time scoring

3. CACHING STRATEGY:

   Cache Structure:
   ```python
   # Cache key format
   key = f"match:{hash(search_params)}"
   
   # Cache value
   {
       "results": [...],  # List of matches
       "timestamp": "2024-12-17T10:00:00Z",
       "ttl": 300  # 5 minutes
   }
   ```
   
   Cache matching results for 5 minutes:
   - Key: hash of search parameters
   - Invalidate when new rides posted in search area
   
   Cache route calculations for 1 hour:
   - Key: origin_coords + destination_coords + waypoints
   - Reuse for similar searches

4. PERFORMANCE OPTIMIZATION:

   Strategies:
   
   A. Database Level:
      - Use indexes on status, departure_time
      - Filter as much as possible in SQL
      - Limit initial results to 100 rides
   
   B. Route Calculations:
      - Use Haversine for initial filtering
      - Only calculate exact routes for top 30 candidates
      - Parallelize route calculations (asyncio.gather)
   
   C. API Call Minimization:
      - Cache aggressively
      - Batch requests when possible
      - Use Haversine estimates when acceptable
   
   Target: < 500ms for typical search

5. API ENDPOINT (ride-service/app/api/routes/rides.py):

   ```python
   POST /api/v1/rides/match
   
   Request:
   {
     "origin": {"lat": x, "lng": y, "address": "..."},
     "destination": {"lat": x, "lng": y, "address": "..."},
     "departure_time_range": {
       "start": "2024-12-25T08:00:00Z",
       "end": "2024-12-25T10:00:00Z"
     },
     "min_seats": 1,
     "max_price": 15.0,
     "preferences": {
       "music": true,
       "ac": true
     }
   }
   
   Response:
   {
     "matches": [
       {
         "ride": {/* ride details */},
         "compatibility": {
           "score": 85,
           "breakdown": {
             "route_score": 38,
             "time_score": 18,
             "price_score": 12,
             "rating_score": 12,
             "preference_score": 5
           },
           "detour": {
             "distance_km": 2.5,
             "time_minutes": 5
           },
           "pickup_distance_km": 1.2,
           "dropoff_distance_km": 0.8,
           "estimated_pickup_time": "2024-12-25T08:15:00Z",
           "estimated_dropoff_time": "2024-12-25T09:00:00Z"
         }
       }
     ],
     "total_matches": 15,
     "search_time_ms": 250
   }
   ```

6. SCORING CONFIGURATION:
   Make scoring weights configurable:
   ```python
   class MatchingConfig:
       ROUTE_SCORE_WEIGHT = 40
       TIME_SCORE_WEIGHT = 20
       PRICE_SCORE_WEIGHT = 15
       RATING_SCORE_WEIGHT = 15
       PREFERENCE_SCORE_WEIGHT = 10
       
       MAX_DETOUR_KM = 15
       MAX_DETOUR_MINUTES = 20
       MAX_PICKUP_DISTANCE_KM = 5
       MAX_DROPOFF_DISTANCE_KM = 5
       DIRECTION_TOLERANCE_DEGREES = 45
   ```

7. LOGGING AND MONITORING:
   Log for each search:
   - Search parameters
   - Number of rides evaluated
   - Number of matches returned
   - Top 3 scores
   - API calls made
   - Cache hit rate
   - Total processing time

8. FUTURE ENHANCEMENTS (Structure Only):
   Prepare for ML:
   - Log all searches and chosen rides
   - Track conversion rate (search → booking)
   - Store features: [route_score, time_score, price, rating, ...]
   - Target: booking probability
   - Can train model later to predict best matches

9. GENERATE LEARNING DOCUMENTATION:
   Create: docs/learning/05-algorithm-design.md
   
   Cover (15-20 pages):
   1. Algorithm Design Principles
      - Problem definition
      - Requirements and constraints
      - Success metrics
   
   2. Multi-Criteria Decision Making
      - Weighted scoring
      - Normalization
      - Trade-offs
   
   3. Geospatial Algorithms
      - Haversine formula (detailed)
      - Bearing calculation
      - Route compatibility
      - Detour calculation
   
   4. Scoring System Design
      - Component selection
      - Weight assignment
      - Score normalization
      - Handling missing data
   
   5. Performance Optimization
      - Time complexity (Big O)
      - Database indexing
      - Caching strategies
      - Parallel processing
      - API call minimization
   
   6. Caching Patterns
      - What to cache
      - Cache keys design
      - TTL selection
      - Invalidation strategies
   
   7. Algorithm Testing
      - Unit tests for components
      - Integration tests
      - Performance tests
      - Edge cases
   
   8. Real-World Considerations
      - User experience
      - Fairness
      - Privacy
      - Bias mitigation
   
   9. Future: Machine Learning
      - Feature engineering
      - Model selection
      - Training pipeline
      - A/B testing

10. TESTING (tests/test_matching.py):
    Create comprehensive tests:
    - test_perfect_match (same route, score ~95+)
    - test_small_detour (score ~80-90)
    - test_large_detour (filtered out)
    - test_opposite_direction (filtered out)
    - test_time_match
    - test_price_filter
    - test_preference_matching
    - test_score_calculation
    - test_ranking_order
    - test_caching
    - test_performance (< 500ms)
    - test_parallel_route_calculation

11. POSTMAN COLLECTION:
    Add "Smart Matching" folder:
    - Match Rides (perfect match scenario)
    - Match Rides (with detour)
    - Match Rides (with preferences)
    - Match Rides (price filter)
    - Match Rides (time range)
    - Match Rides (no matches)

VERIFICATION CHECKLIST:
- [ ] Algorithm implemented
- [ ] Perfect match scores 90+
- [ ] Small detour scores 75-85
- [ ] Large detour filtered out
- [ ] Opposite direction filtered
- [ ] Time scoring works
- [ ] Price scoring works
- [ ] Rating scoring works
- [ ] Preference matching works
- [ ] Total score calculated correctly
- [ ] Results sorted by score
- [ ] Score breakdown included
- [ ] Detour info included
- [ ] Caching works
- [ ] Cache hit rate > 80%
- [ ] Search time < 500ms
- [ ] API calls minimized (< 5 per search)
- [ ] All tests pass
- [ ] Learning doc complete

Please generate matching service with comprehensive algorithm and tests.
```

---

## TESTING CHECKLIST - SECTION 5

### Algorithm Implementation
- [ ] Matching service created
- [ ] All scoring components implemented
- [ ] Weights configurable

### Scoring Tests

#### Perfect Match
Search: SJSU → SF Airport
Ride: SJSU → SF Airport (exact same)
- [ ] Score: 90-100
- [ ] Route score: 40 (no detour)
- [ ] Time score: 20 (exact match)
- [ ] Includes in results

#### Small Detour
Search: SJSU → SF Airport  
Ride: Downtown SJ → SF Airport
- [ ] Score: 75-85
- [ ] Route score: 30-35 (small detour)
- [ ] Included in results
- [ ] Detour info correct

#### Large Detour
Search: SJSU → SF Airport
Ride: East Bay → SF Airport (opposite direction)
- [ ] Filtered out (detour > 15 km)
- [ ] Not in results

#### Time Scoring
- [ ] Exact time: 20 points
- [ ] 15 min diff: 15 points
- [ ] 30 min diff: 10 points
- [ ] 1 hour diff: 5 points

#### Price Scoring
- [ ] Free ride: 15 points
- [ ] $5 ride: 12 points
- [ ] $15 ride: 5 points

#### Preference Matching
Ride: {music: true, ac: true}
Search: {music: true, ac: true}
- [ ] Score: 10 points (perfect match)

Ride: {music: false}
Search: {music: true}
- [ ] Score: 0 points (conflict)

### Performance
- [ ] Search time < 500ms (typical)
- [ ] Search time < 1000ms (complex)
- [ ] Parallel route calculations work
- [ ] Database queries optimized

### Caching
- [ ] First search calls API
- [ ] Second search uses cache
- [ ] Cache key consistent
- [ ] Cache expires after 5 min
- [ ] Route cache works (1 hour)
- [ ] Cache hit rate > 80%

### API Endpoint
- [ ] POST /api/v1/rides/match works
- [ ] Returns sorted results
- [ ] Includes score breakdown
- [ ] Includes detour info
- [ ] Includes estimated times
- [ ] Response time acceptable

### Edge Cases
- [ ] No matching rides: returns empty array
- [ ] All rides full: filtered out
- [ ] Past departure time: filtered
- [ ] Invalid coordinates: validation error

### Integration
- [ ] Works with Google Maps API
- [ ] Handles API failures gracefully
- [ ] Falls back to Haversine if needed

### Learning
- [ ] Read 05-algorithm-design.md
- [ ] Understand scoring system
- [ ] Understand optimization techniques
- [ ] Can explain algorithm to someone

### Completion
- [ ] All tests passing
- [ ] Performance targets met
- [ ] Caching working
- [ ] Documentation complete
- [ ] Ready for Section 6

---

**Date Completed:** _______________  
**Search Time (avg):** _______ ms  
**Cache Hit Rate:** _______ %  
**Notes:** _______________
