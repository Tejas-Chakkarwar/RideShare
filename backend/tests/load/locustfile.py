"""
Load testing with Locust
Simulates concurrent users for performance testing

Run: locust -f backend/tests/load/locustfile.py --host=http://localhost:8002
Web UI: http://localhost:8089
"""
from locust import HttpUser, task, between
import random


class RideShareUser(HttpUser):
    """Simulates a typical SJSU RideShare user"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Login on start (simulate authenticated user)"""
        # In real scenario, create test users first
        self.token = None
        # For load testing, you'd want to:
        # 1. Pre-create test users
        # 2. Login and store token
        # 3. Use token for authenticated requests

    @task(5)
    def search_rides(self):
        """Simulate ride search (most common operation - 50% of traffic)"""
        # Random SJSU campus locations
        origins = [
            (37.3371, -121.8818),  # North Garage
            (37.3357, -121.8849),  # MLK Library
            (37.3365, -121.8813),  # Student Union
        ]
        destinations = [
            (37.3297, -121.9026),  # Diridon Station
            (37.3639, -121.9289),  # SJC Airport
            (37.3325, -121.8815),  # South Garage
        ]

        origin = random.choice(origins)
        dest = random.choice(destinations)

        self.client.get("/api/v1/rides/", params={
            "origin_lat": origin[0],
            "origin_lng": origin[1],
            "destination_lat": dest[0],
            "destination_lng": dest[1]
        }, name="/api/v1/rides/search")

    @task(2)
    def view_campus_locations(self):
        """View campus locations (20% of traffic)"""
        self.client.get("/api/v1/sjsu/campus-locations")

    @task(1)
    def search_campus_locations(self):
        """Search campus locations (10%)"""
        queries = ["library", "parking", "garage", "stadium"]
        query = random.choice(queries)
        self.client.get(f"/api/v1/sjsu/campus-locations/search?q={query}")

    @task(1)
    def view_upcoming_events(self):
        """View upcoming events (10%)"""
        self.client.get("/api/v1/sjsu/events/upcoming")

    @task(1)
    def get_user_profile(self):
        """Get user profile (10%)"""
        if self.token:
            self.client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )


class HeavyLoadUser(HttpUser):
    """Simulates heavy traffic during peak hours (8-9 AM, 4-5 PM)"""
    wait_time = between(0.5, 1.5)  # Faster requests

    @task
    def rapid_search(self):
       """Rapid ride searches"""
       self.client.get("/api/v1/rides/", params={
            "origin_lat": 37.3357,
            "origin_lng": -121.8849
        })
