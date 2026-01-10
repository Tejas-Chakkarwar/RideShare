# SJSU RideShare Development Guide
## Section 12: Advanced UX Features

**Version:** 1.0
**Duration:** Week 12 (5-6 days)
**Focus:** Saved Locations, Ride History, Advanced Search, Driver Dashboard

---

# OVERVIEW

This section implements "quality of life" features that dramatically improve user experience:
- **Saved Locations** (Home, Work, SJSU) - Quick wins, high impact
- **Ride History & Receipts** (PDF generation)
- **Advanced Search Filters** (Rating, gender, amenities)
- **Driver Dashboard** (Earnings, statistics)
- **Ride Templates** (Recurring commutes)

---

# PART 1: SAVED LOCATIONS

## Database Model

**File:** `backend/services/user-service/app/models/saved_location.py`

```python
from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import uuid
from app.db.base import Base


class SavedLocation(Base):
    """User's saved locations for quick selection"""
    __tablename__ = "saved_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Location details
    name = Column(String(50), nullable=False)  # "Home", "Work", "SJSU", "Gym"
    address = Column(String(500), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Category/Icon
    category = Column(String(20), nullable=False)  # "home", "work", "school", "custom"
    icon = Column(String(50), default="location_pin")

    # Usage tracking
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## API Endpoints

```python
# POST /api/v1/users/me/saved-locations
# GET /api/v1/users/me/saved-locations
# PUT /api/v1/saved-locations/{id}
# DELETE /api/v1/saved-locations/{id}
```

**Implementation Time:** 2 days

---

# PART 2: RIDE HISTORY & RECEIPTS

## PDF Receipt Generation

**File:** `backend/services/booking-service/app/utils/pdf_generator.py`

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime


def generate_receipt_pdf(booking: dict, ride: dict, passenger: dict) -> bytes:
    """
    Generate PDF receipt for a booking.

    Returns: PDF as bytes
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 750, "SJSU RideShare Receipt")

    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Receipt ID: RCPT-{str(booking['id'])[:8]}")
    c.drawString(50, 700, f"Date: {datetime.now().strftime('%B %d, %Y')}")

    # Passenger info
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 660, "Passenger Information")
    c.setFont("Helvetica", 11)
    c.drawString(50, 640, f"Name: {passenger.get('full_name', 'N/A')}")
    c.drawString(50, 625, f"Email: {passenger.get('email', 'N/A')}")

    # Ride details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 590, "Ride Details")
    c.setFont("Helvetica", 11)
    c.drawString(50, 570, f"From: {booking['pickup_location']['address']}")
    c.drawString(50, 555, f"To: {booking['dropoff_location']['address']}")
    c.drawString(50, 540, f"Seats: {booking['seats_booked']}")

    # Payment
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 500, "Payment Summary")
    c.setFont("Helvetica", 11)
    c.drawString(50, 480, f"Fare: ${float(booking['total_amount']):.2f}")
    c.drawString(50, 465, f"Payment Method: Stripe")
    c.drawString(50, 450, f"Status: Paid")

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 50, "Thank you for riding with SJSU RideShare!")

    c.save()
    buffer.seek(0)
    return buffer.read()
```

## API Endpoint

```python
from fastapi.responses import StreamingResponse

@router.get("/{booking_id}/receipt-pdf")
async def download_receipt_pdf(
    booking_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Download booking receipt as PDF"""
    booking = await service.get_booking(booking_id)

    # Authorization check
    if str(booking.passenger_id) != str(current_user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get ride and passenger details
    ride = await ride_client.get_ride(booking.ride_id)
    passenger = await user_client.get_user(current_user_id)

    # Generate PDF
    pdf_bytes = generate_receipt_pdf(booking.to_dict(), ride, passenger)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{booking_id}.pdf"
        }
    )
```

**Implementation Time:** 3 days

---

# PART 3: ADVANCED SEARCH FILTERS

## Enhanced Search Schema

**File:** `backend/services/ride-service/app/schemas/ride.py`

Update `RideSearchParams`:

```python
class RideSearchParams(BaseModel):
    # Existing geospatial filters
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    proximity_km: float = Field(5.0, ge=0.1, le=50.0)

    # Time filters
    departure_date: Optional[str] = None
    departure_time_start: Optional[str] = None  # "08:00"
    departure_time_end: Optional[str] = None    # "10:00"

    # Capacity
    min_seats: int = Field(1, ge=1, le=7)

    # Price filters
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)

    # Driver rating filter (requires ratings to be implemented first)
    min_driver_rating: Optional[float] = Field(None, ge=1.0, le=5.0)

    # Driver preferences
    driver_gender: Optional[str] = Field(None, pattern="^(male|female|other|any)$")

    # Vehicle preferences
    amenities: Optional[List[str]] = None  # ["ac", "music", "usb_charger"]

    # Sorting
    sort_by: str = Field(
        "departure_time",
        pattern="^(departure_time|price_per_seat|created_at|driver_rating)$"
    )
    sort_order: str = Field("asc", pattern="^(asc|desc)$")

    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
```

## Updated Matching Service

```python
async def search_rides(
    self,
    search_params: RideSearchParams,
    db: AsyncSession
) -> List[Ride]:
    """Enhanced ride search with all filters"""

    query = select(Ride).where(
        Ride.status == RideStatus.ACTIVE,
        Ride.available_seats >= search_params.min_seats
    )

    # Price filters
    if search_params.min_price:
        query = query.where(Ride.price_per_seat >= search_params.min_price)
    if search_params.max_price:
        query = query.where(Ride.price_per_seat <= search_params.max_price)

    # Time filters
    if search_params.departure_date:
        date = datetime.fromisoformat(search_params.departure_date)
        query = query.where(func.date(Ride.departure_time) == date.date())

    # Driver rating filter (join with user ratings)
    if search_params.min_driver_rating:
        # Requires rating system to be implemented
        query = query.join(User, Ride.driver_id == User.id).where(
            User.average_rating_as_driver >= search_params.min_driver_rating
        )

    # Execute query and apply post-filters
    result = await db.execute(query)
    rides = result.scalars().all()

    # Geospatial filtering
    if search_params.origin_lat and search_params.origin_lng:
        rides = [
            ride for ride in rides
            if haversine_distance(
                ride.origin_lat, ride.origin_lng,
                search_params.origin_lat, search_params.origin_lng
            ) <= search_params.proximity_km
        ]

    # Sort
    if search_params.sort_by == "price_per_seat":
        rides.sort(key=lambda r: r.price_per_seat, reverse=(search_params.sort_order == "desc"))
    elif search_params.sort_by == "departure_time":
        rides.sort(key=lambda r: r.departure_time, reverse=(search_params.sort_order == "desc"))

    # Pagination
    return rides[search_params.skip:search_params.skip + search_params.limit]
```

**Implementation Time:** 3-4 days

---

# PART 4: DRIVER DASHBOARD

## Dashboard Service

**File:** `backend/services/booking-service/app/services/dashboard_service.py`

```python
class DriverDashboardService:
    """Service for driver analytics and insights"""

    async def get_driver_dashboard(
        self,
        driver_id: UUID,
        period: str = "week",  # "day", "week", "month"
        db: AsyncSession
    ) -> dict:
        """
        Get comprehensive driver dashboard data.

        Returns:
        - Total earnings (gross, platform fee, net)
        - Ride statistics (total rides, completion rate)
        - Upcoming bookings
        - Recent reviews
        - Performance metrics
        """
        # Calculate date range
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)

        # Get all bookings for this driver's rides
        from app.models.booking import Booking, BookingStatus

        result = await db.execute(
            select(Booking)
            .join(Ride, Booking.ride_id == Ride.id)
            .where(
                Ride.driver_id == driver_id,
                Booking.created_at >= start_date
            )
        )
        bookings = result.scalars().all()

        # Calculate earnings
        total_earnings = sum(
            float(b.driver_payout or 0)
            for b in bookings
            if b.status == BookingStatus.COMPLETED
        )

        total_platform_fees = sum(
            float(b.platform_fee or 0)
            for b in bookings
            if b.status == BookingStatus.COMPLETED
        )

        # Ride statistics
        completed_rides = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
        cancelled_rides = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
        completion_rate = (
            completed_rides / len(bookings) * 100
            if bookings else 0
        )

        # Get upcoming bookings
        upcoming = await db.execute(
            select(Booking)
            .join(Ride, Booking.ride_id == Ride.id)
            .where(
                Ride.driver_id == driver_id,
                Booking.status == BookingStatus.PENDING
            )
            .limit(10)
        )
        upcoming_bookings = upcoming.scalars().all()

        return {
            "period": period,
            "earnings": {
                "gross": total_earnings + total_platform_fees,
                "platform_fees": total_platform_fees,
                "net": total_earnings,
                "currency": "USD"
            },
            "statistics": {
                "total_rides": len(bookings),
                "completed": completed_rides,
                "cancelled": cancelled_rides,
                "completion_rate": round(completion_rate, 2)
            },
            "upcoming_bookings_count": len(upcoming_bookings),
            "average_rating": 0.0,  # Get from ratings service
            "badges": []  # Get from user service
        }
```

## API Endpoint

```python
@router.get("/drivers/me/dashboard")
async def get_my_driver_dashboard(
    period: str = "week",
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get driver dashboard with earnings and statistics.

    Query Parameters:
    - period: "day", "week", "month"
    """
    from app.services.dashboard_service import dashboard_service

    return await dashboard_service.get_driver_dashboard(
        current_user_id,
        period,
        db
    )
```

**Implementation Time:** 4-5 days

---

# PART 5: RIDE TEMPLATES

Quick feature for recurring commutes.

## Model

```python
class RideTemplate(Base):
    """Template for frequently created rides"""
    __tablename__ = "ride_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(100), nullable=False)  # "Mon/Wed to SJSU"
    template_data = Column(JSON, nullable=False)  # Stores full ride creation data

    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## API

```python
# POST /api/v1/rides/templates (create template)
# GET /api/v1/rides/templates (list templates)
# POST /api/v1/rides/from-template/{template_id} (create ride from template)
```

**Implementation Time:** 1-2 days

---

# COMPLETE PROMPT FOR CLAUDE CODE

```
PROJECT: SJSU RideShare - Section 12: Advanced UX Features

IMPLEMENT:

1. SAVED LOCATIONS:
   - Create SavedLocation model
   - CRUD API for saved locations
   - Usage tracking

2. RIDE HISTORY:
   - PDF receipt generation (ReportLab)
   - Trip statistics aggregation
   - Export data endpoint (GDPR)

3. ADVANCED SEARCH:
   - Add filters to RideSearchParams
   - Update matching service with new filters
   - Support rating, gender, amenities filters

4. DRIVER DASHBOARD:
   - Earnings aggregation by period
   - Ride statistics (completion rate)
   - Upcoming bookings preview
   - Performance metrics

5. RIDE TEMPLATES:
   - Simple model for saved ride configs
   - Create ride from template

PRIORITY ORDER:
1. Saved Locations (quick win, 2 days)
2. Ride Templates (quick win, 1-2 days)
3. Advanced Search (3-4 days)
4. Ride History & PDF (3 days)
5. Driver Dashboard (4-5 days)

Install dependencies:
```bash
pip install reportlab  # For PDF generation
```

Use code structures above. Add proper error handling.
```

---

# COMPLETION CHECKLIST

- [ ] Saved locations CRUD implemented
- [ ] Ride templates created
- [ ] Advanced search filters working
- [ ] PDF receipt generation functional
- [ ] Driver dashboard with earnings
- [ ] All features tested
- [ ] Database migrations run
- [ ] API documentation updated

---

**Next:** Section 13 - SJSU-Specific Features & Launch Preparation
