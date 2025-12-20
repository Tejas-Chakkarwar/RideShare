# SJSU RideShare Development Guide
## Section 6: Booking Service

**Version:** 1.0  
**Duration:** Week 6  
**Focus:** Booking management, seat reservation, state machine, transactions

---

# SECTION 6: Booking Service

## Learning Objectives
- Build booking microservice from scratch
- Implement request/approval workflow
- Handle database transactions (ACID)
- Manage state machines
- Prevent race conditions with locking
- Implement seat management system
- Inter-service coordination

## Technologies
- FastAPI (new service)
- SQLAlchemy transactions
- State machine patterns
- Pessimistic/Optimistic locking
- Async database operations
- Redis for distributed locks (optional)

## Prerequisites
- Sections 1-5 completed ✅
- Understanding of database transactions
- Understanding of concurrency issues
- Knowledge of state machines
- Ride service running

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Booking Service Microservice

CONTEXT:
Sections 1-5 completed. Users can search and match rides.
Now creating booking-service for managing ride bookings with request/approval workflow.
Section 6 of 13.

GOAL:
Build booking-service that handles:
- Booking requests from passengers
- Approval/rejection by drivers
- Seat availability management (prevent overbooking)
- Cancellation with policies
- State management
- Race condition prevention

DETAILED REQUIREMENTS:

1. CREATE BOOKING-SERVICE STRUCTURE:
   
   backend/services/booking-service/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── api/routes/
   │   │   ├── health.py
   │   │   └── bookings.py
   │   ├── core/
   │   │   ├── config.py
   │   │   ├── database.py
   │   │   └── exceptions.py
   │   ├── models/
   │   │   └── booking.py
   │   ├── schemas/
   │   │   └── booking.py
   │   ├── services/
   │   │   ├── booking_service.py
   │   │   └── seat_manager.py
   │   └── clients/
   │       ├── ride_client.py
   │       ├── user_client.py
   │       └── notification_client.py
   ├── alembic/
   ├── tests/
   ├── Dockerfile
   ├── requirements.txt
   └── README.md

2. BOOKING MODEL (app/models/booking.py):

   Fields:
   - id: UUID (primary key)
   - ride_id: UUID (foreign key to rides.id)
   - passenger_id: UUID (foreign key to users.id)
   - seats_booked: Integer (1-7)
   - pickup_location: JSON {"lat": x, "lng": y, "address": "..."}
   - dropoff_location: JSON
   - estimated_pickup_time: DateTime
   - estimated_dropoff_time: DateTime
   - actual_pickup_time: DateTime (nullable, set when ride starts)
   - actual_dropoff_time: DateTime (nullable, set when completed)
   - status: Enum ("pending", "approved", "rejected", "cancelled", "completed")
   - amount: Numeric(10,2) (total price)
   - payment_status: Enum ("pending", "held", "completed", "refunded")
   - payment_intent_id: String (Stripe ID - for Section 9)
   - passenger_notes: Text (optional message to driver)
   - driver_notes: Text (optional response)
   - cancellation_reason: Text
   - cancelled_by: Enum ("passenger", "driver", "system")
   - cancelled_at: DateTime (nullable)
   - created_at, updated_at: DateTime
   
   Indexes:
   - (ride_id, passenger_id) composite
   - passenger_id
   - status
   - created_at
   
   Constraints:
   - seats_booked > 0 AND seats_booked <= 7
   - amount >= 0
   - Unique: (ride_id, passenger_id) WHERE status IN ('pending', 'approved')

3. BOOKING SCHEMAS (app/schemas/booking.py):

   BookingCreate:
   - ride_id: UUID
   - seats_booked: int (1-7)
   - pickup_location: dict
   - dropoff_location: dict
   - passenger_notes: Optional[str] (max 500 chars)
   
   BookingUpdate:
   - All fields optional
   - Only allowed if status = "pending"
   
   BookingResponse:
   - All booking fields
   - ride_info: dict (from ride-service)
   - passenger_info: dict (from user-service)
   
   BookingApproval:
   - driver_notes: Optional[str]
   - estimated_pickup_time: DateTime
   - estimated_dropoff_time: DateTime
   
   BookingRejection:
   - driver_notes: str (required, reason)
   
   BookingCancellation:
   - cancellation_reason: str (required)

4. SEAT MANAGER (app/services/seat_manager.py):

   Purpose: Handle seat availability with concurrency control
   
   Key Functions:
   
   A. check_seat_availability(ride_id, seats_requested, db) -> bool:
      - Get ride details from ride-service
      - Query bookings: SELECT SUM(seats_booked) WHERE ride_id AND status IN ('pending', 'approved')
      - Calculate: available = ride.available_seats - total_booked
      - Return: available >= seats_requested
   
   B. reserve_seats(ride_id, seats, booking_id, db) -> bool:
      - Use database transaction with locking
      - Check availability
      - Create booking with status="pending"
      - Commit transaction
      - Handle race conditions
   
   C. release_seats(booking_id, db) -> None:
      - Get booking
      - Update status to "cancelled"
      - Seats automatically available again
   
   D. update_ride_status(ride_id, db) -> None:
      - Calculate total booked seats
      - If all seats booked: update ride status to "full"
      - If previously full and now has seats: update to "active"
      - Call ride-service API to update

5. BOOKING SERVICE (app/services/booking_service.py):

   Key Functions:
   
   A. create_booking(booking_data, passenger_id, db) -> Booking:
      ```python
      - Verify ride exists and is active (call ride-service)
      - Verify departure_time is in future (> 1 hour from now)
      - Check seat availability
      - Calculate amount (seats * price_per_seat)
      - Use transaction:
          * Reserve seats (with lock)
          * Create booking with status="pending"
          * Commit
      - Send notification to driver (call notification-service)
      - Return booking
      - Handle errors:
          * RideNotFoundException
          * InsufficientSeatsException
          * RideAlreadyStartedException
      ```
   
   B. approve_booking(booking_id, approval_data, driver_id, db) -> Booking:
      ```python
      - Get booking
      - Verify ride belongs to driver (call ride-service)
      - Verify booking status is "pending"
      - Update:
          * status = "approved"
          * estimated_pickup_time = approval_data.estimated_pickup_time
          * estimated_dropoff_time = approval_data.estimated_dropoff_time
          * driver_notes = approval_data.driver_notes
      - Update ride seat count
      - Send notification to passenger (approval)
      - Return booking
      ```
   
   C. reject_booking(booking_id, rejection_data, driver_id, db) -> Booking:
      ```python
      - Get booking
      - Verify ride belongs to driver
      - Verify status is "pending"
      - Update:
          * status = "rejected"
          * driver_notes = rejection_data.driver_notes
      - Release seats
      - Send notification to passenger (rejection)
      - Return booking
      ```
   
   D. cancel_booking_by_passenger(booking_id, cancellation_data, passenger_id, db) -> Booking:
      ```python
      - Get booking
      - Verify belongs to passenger
      - Check cancellation policy:
          * > 24 hours before ride: free cancellation
          * 2-24 hours: 50% refund
          * < 2 hours: no refund
      - Update:
          * status = "cancelled"
          * cancelled_by = "passenger"
          * cancellation_reason
          * cancelled_at = now
      - Release seats
      - Handle refund (if applicable - Section 9)
      - Send notification to driver
      - Return booking
      ```
   
   E. cancel_booking_by_driver(booking_id, cancellation_data, driver_id, db) -> Booking:
      ```python
      - Similar to passenger cancellation
      - Driver can cancel anytime (full refund to passenger)
      - cancelled_by = "driver"
      - Send notification to passenger
      ```
   
   F. complete_booking(booking_id, driver_id, db) -> Booking:
      ```python
      - After ride completed
      - Update:
          * status = "completed"
          * actual_pickup_time = now (or provided)
          * actual_dropoff_time = now (or provided)
          * payment_status = "completed"
      - Release payment to driver (Section 9)
      - Prompt for reviews
      - Return booking
      ```

6. STATE MACHINE:

   Valid State Transitions:
   ```
   pending → approved (by driver)
   pending → rejected (by driver)
   pending → cancelled (by passenger before approval)
   
   approved → cancelled (by passenger or driver)
   approved → completed (by driver after ride)
   
   completed → (final state, no transitions)
   rejected → (final state, no transitions)
   cancelled → (final state, no transitions)
   ```
   
   Implement validation:
   ```python
   def validate_state_transition(current_state, new_state) -> bool:
       allowed_transitions = {
           "pending": ["approved", "rejected", "cancelled"],
           "approved": ["cancelled", "completed"],
           "completed": [],
           "rejected": [],
           "cancelled": []
       }
       return new_state in allowed_transitions.get(current_state, [])
   ```

7. RACE CONDITION HANDLING:

   Scenario: Two passengers try to book the last seat simultaneously
   
   Solution: Pessimistic Locking
   ```python
   async def reserve_seats_with_lock(ride_id, seats, db):
       # Start transaction
       async with db.begin():
           # Lock the ride row
           result = await db.execute(
               select(Ride)
               .where(Ride.id == ride_id)
               .with_for_update()  # FOR UPDATE lock
           )
           ride = result.scalar_one_or_none()
           
           if not ride:
               raise RideNotFoundException()
           
           # Calculate available seats
           booked = await db.execute(
               select(func.sum(Booking.seats_booked))
               .where(Booking.ride_id == ride_id)
               .where(Booking.status.in_(["pending", "approved"]))
           )
           total_booked = booked.scalar() or 0
           available = ride.available_seats - total_booked
           
           if available < seats:
               raise InsufficientSeatsException()
           
           # Create booking
           booking = Booking(...)
           db.add(booking)
           
           # Commit releases lock
       
       return booking
   ```

8. CANCELLATION POLICY:

   Time before ride departure:
   - > 24 hours: Free cancellation (100% refund)
   - 2-24 hours: 50% refund
   - < 2 hours: No refund
   - Driver cancellation: Always 100% refund to passengers
   
   Implementation:
   ```python
   def calculate_refund_amount(booking, cancellation_time):
       time_until_ride = booking.estimated_pickup_time - cancellation_time
       hours_until_ride = time_until_ride.total_seconds() / 3600
       
       if hours_until_ride >= 24:
           return booking.amount  # 100%
       elif hours_until_ride >= 2:
           return booking.amount * 0.5  # 50%
       else:
           return 0  # No refund
   ```

9. API ROUTES (app/api/routes/bookings.py):

   POST /api/v1/bookings (protected):
   - Create booking request
   - Returns 201 with BookingResponse
   
   GET /api/v1/bookings/{booking_id} (protected):
   - Get booking details
   - Only accessible by passenger, driver, or admin
   - Returns 200 with BookingResponse
   
   PUT /api/v1/bookings/{booking_id} (protected):
   - Update booking (passenger only, before approval)
   - Returns 200 with BookingResponse
   
   POST /api/v1/bookings/{booking_id}/approve (protected):
   - Approve booking (driver only)
   - Returns 200 with BookingResponse
   
   POST /api/v1/bookings/{booking_id}/reject (protected):
   - Reject booking (driver only)
   - Returns 200 with BookingResponse
   
   POST /api/v1/bookings/{booking_id}/cancel (protected):
   - Cancel booking (passenger or driver)
   - Returns 200 with BookingResponse
   
   POST /api/v1/bookings/{booking_id}/complete (protected):
   - Mark booking complete (driver only, after ride)
   - Returns 200 with BookingResponse
   
   GET /api/v1/bookings/passenger/me (protected):
   - Get current passenger's bookings
   - Query param: status (optional filter)
   - Returns 200 with List[BookingResponse]
   
   GET /api/v1/bookings/ride/{ride_id} (protected):
   - Get all bookings for a ride (driver only)
   - Returns 200 with List[BookingResponse]
   
   GET /api/v1/bookings/ride/{ride_id}/statistics (protected):
   - Get booking statistics (driver only)
   - Returns: total_requests, approved, rejected, seats_booked, revenue

10. INTER-SERVICE CLIENTS:

    A. ride_client.py:
       - get_ride(ride_id) -> dict
       - verify_driver_owns_ride(ride_id, driver_id) -> bool
       - update_ride_status(ride_id, status) -> None
    
    B. user_client.py:
       - get_user(user_id) -> dict
    
    C. notification_client.py:
       - send_booking_request_notification(driver_id, booking)
       - send_booking_approved_notification(passenger_id, booking)
       - send_booking_rejected_notification(passenger_id, booking)
       - send_booking_cancelled_notification(user_id, booking)

11. DOCKER CONFIGURATION:
    
    Update docker-compose.yml:
    ```yaml
    booking-service:
      build: ./services/booking-service
      ports: ["8003:8000"]
      environment:
        - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare
        - RIDE_SERVICE_URL=http://ride-service:8000
        - USER_SERVICE_URL=http://user-service:8000
        - NOTIFICATION_SERVICE_URL=http://notification-service:8000
      depends_on: [postgres, redis, ride-service, user-service]
    ```

12. ALEMBIC MIGRATION:
    - Create migration: 001_create_bookings_table.py
    - Create bookings table with all fields
    - Create indexes
    - Create enums (BookingStatus, PaymentStatus, CancelledBy)
    - Create constraints

13. CUSTOM EXCEPTIONS:
    - BookingNotFoundException
    - InsufficientSeatsException
    - InvalidStateTransitionException
    - UnauthorizedException
    - RideAlreadyStartedException
    - CancellationNotAllowedException

14. GENERATE LEARNING DOCUMENTATION:
    
    Create: docs/learning/06-transactions-and-state-management.md
    
    Cover (20+ pages):
    1. Database Transactions (ACID)
       - Atomicity, Consistency, Isolation, Durability
       - Transaction examples
       - When to use transactions
    
    2. Concurrency and Race Conditions
       - What are race conditions?
       - The "last seat" problem
       - Real-world examples
    
    3. Locking Strategies
       - Pessimistic locking (FOR UPDATE)
       - Optimistic locking (version numbers)
       - Distributed locking (Redis)
       - Deadlocks and prevention
       - Lock timeout handling
    
    4. State Machines
       - What is a state machine?
       - States and transitions
       - State validation
       - Implementation patterns
       - Diagram of booking states
    
    5. Transaction Isolation Levels
       - Read Uncommitted
       - Read Committed
       - Repeatable Read
       - Serializable
       - PostgreSQL defaults
    
    6. Idempotency
       - What is idempotency?
       - Why it matters for APIs
       - Implementing idempotent operations
       - Idempotency keys
    
    7. Error Handling in Transactions
       - Rollback strategies
       - Partial failures
       - Compensation patterns
       - Saga pattern (intro)
    
    8. Inter-Service Consistency
       - Distributed transactions challenges
       - Eventual consistency
       - Two-phase commit (2PC)
       - Saga pattern detailed
    
    9. Best Practices
       - Keep transactions short
       - Handle deadlocks gracefully
       - Retry strategies
       - Logging and monitoring
       - Testing concurrent operations
    
    10. Code Examples
        - Transaction with lock
        - State machine implementation
        - Race condition test
        - Deadlock handling

15. TESTING (tests/test_bookings.py):

    Comprehensive tests:
    - test_create_booking_success
    - test_create_booking_insufficient_seats
    - test_create_booking_ride_not_found
    - test_create_booking_past_ride
    - test_approve_booking_driver
    - test_approve_booking_not_driver (403)
    - test_reject_booking
    - test_cancel_booking_passenger_early (full refund)
    - test_cancel_booking_passenger_late (no refund)
    - test_cancel_booking_driver (full refund)
    - test_complete_booking
    - test_race_condition_last_seat (critical!)
    - test_invalid_state_transition
    - test_update_booking_after_approval (should fail)
    - test_get_passenger_bookings
    - test_get_ride_bookings_driver
    - test_booking_statistics

16. POSTMAN COLLECTION:
    
    Add "Bookings" folder:
    - Create Booking (valid)
    - Create Booking (insufficient seats)
    - Create Booking (invalid ride)
    - Get Booking by ID
    - Update Booking (before approval)
    - Approve Booking (as driver)
    - Reject Booking (as driver)
    - Cancel Booking (as passenger, early)
    - Cancel Booking (as passenger, late)
    - Cancel Booking (as driver)
    - Complete Booking
    - Get My Bookings (passenger)
    - Get Ride Bookings (driver)
    - Get Booking Statistics

17. LOAD TESTING:
    Test concurrent bookings:
    ```bash
    # Use Apache Bench or similar
    # 10 concurrent users trying to book last seat
    ab -n 10 -c 10 -T application/json -p booking.json \
       http://localhost:8003/api/v1/bookings
    
    # Only 1 should succeed
    ```

CRITICAL REQUIREMENTS:

Transaction Management:
- All seat operations in transactions
- Proper rollback on errors
- Lock timeout handling (10 seconds)
- Isolation level: READ COMMITTED

State Validation:
- Validate every state transition
- Log all state changes
- Prevent invalid transitions

Race Condition Prevention:
- Use FOR UPDATE locks
- Test with concurrent requests
- Verify only one succeeds for last seat

Error Handling:
- Specific exceptions for each error type
- Proper HTTP status codes
- User-friendly error messages
- Comprehensive logging

VERIFICATION CHECKLIST:
- [ ] Booking-service runs on port 8003
- [ ] Can create booking (authenticated)
- [ ] Insufficient seats rejected
- [ ] Can approve booking (driver)
- [ ] Can't approve others' bookings (403)
- [ ] Can reject booking
- [ ] Can cancel (passenger early): full refund
- [ ] Can cancel (passenger late): policy applied
- [ ] Can cancel (driver): full refund
- [ ] State transitions validated
- [ ] Invalid transitions blocked
- [ ] Race condition handled (last seat test)
- [ ] Only one booking succeeds for last seat
- [ ] Seats released on cancellation
- [ ] Ride status updated correctly
- [ ] Inter-service calls work
- [ ] Notifications sent
- [ ] All tests pass
- [ ] Load test passed

Please generate booking service with robust transaction handling and concurrency control.
```

---

## TESTING CHECKLIST - SECTION 6

### Setup
- [ ] Booking-service created
- [ ] Port 8003 configured
- [ ] Dependencies installed
- [ ] Migrations run
- [ ] Bookings table exists

### Basic CRUD
- [ ] Create booking: 201
- [ ] Get booking by ID: 200
- [ ] Update booking (before approval): 200
- [ ] Update booking (after approval): 400

### Seat Management
- [ ] 3 seats available, book 2: success
- [ ] 1 seat available, book 2: fail
- [ ] Book last seat: success
- [ ] Try booking when full: fail

### Approval/Rejection
- [ ] Driver approves: 200
- [ ] Non-driver approves: 403
- [ ] Approve pending: success
- [ ] Approve rejected: fail
- [ ] Driver rejects: 200
- [ ] Seats released on rejection

### Cancellation Policy
- [ ] Cancel 25 hours before: full refund
- [ ] Cancel 12 hours before: 50% refund
- [ ] Cancel 1 hour before: no refund
- [ ] Driver cancel: full refund always

### State Machine
- [ ] Pending → Approved: allowed
- [ ] Pending → Rejected: allowed
- [ ] Approved → Completed: allowed
- [ ] Completed → Cancelled: blocked
- [ ] Rejected → Approved: blocked

### Race Conditions (CRITICAL)

Test Setup: Create ride with 1 seat available

Test: 10 concurrent booking requests

Expected Result:
- [ ] Only 1 booking succeeds (201)
- [ ] 9 bookings fail (400 insufficient seats)
- [ ] Database shows only 1 booking
- [ ] No overbooking occurred

Verification:
```bash
# Check bookings count
SELECT COUNT(*) FROM bookings WHERE ride_id = '{ride_id}' AND status = 'pending';
# Should return 1

# Check seats
SELECT SUM(seats_booked) FROM bookings WHERE ride_id = '{ride_id}';
# Should equal ride.available_seats
```

### Transaction Rollback
- [ ] Create booking fails midway: rollback
- [ ] Database consistent after error
- [ ] No partial data

### Inter-Service Communication
- [ ] Calls ride-service: success
- [ ] Calls user-service: success
- [ ] Calls notification-service: success
- [ ] Handles service down gracefully

### Statistics
- [ ] Get ride statistics: correct counts
- [ ] Total requests accurate
- [ ] Revenue calculated correctly

### Performance
- [ ] Create booking < 200ms
- [ ] Approve booking < 100ms
- [ ] Concurrent requests handled

### Learning
- [ ] Read 06-transactions-and-state-management.md
- [ ] Understand ACID properties
- [ ] Understand locking strategies
- [ ] Understand state machines
- [ ] Can explain race conditions

### Completion
- [ ] All tests passing
- [ ] Race condition test passed
- [ ] State machine working
- [ ] Transactions working
- [ ] Ready for Section 7

---

**Date Completed:** _______________  
**Race Condition Test Result:** Pass / Fail  
**Issues Encountered:** _______________  
**Notes:** _______________
