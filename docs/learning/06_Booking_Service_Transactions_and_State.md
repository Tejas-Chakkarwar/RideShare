# Section 6: Booking Service - Transactions and State Management

**Prerequisites**: You should have completed `00_Complete_Technology_Guide.md`, `02_Advanced_Topics_Migrations_and_Microservices.md`, `03_Google_Maps_Integration.md`, and `04_Smart_Matching_Algorithm.md`.

---

## Table of Contents

### Part 1: Database Transactions (ACID)
1. What are Database Transactions?
2. ACID Properties Explained
3. Why Transactions Matter for Bookings
4. Transaction Lifecycle
5. Commit vs Rollback

### Part 2: Concurrency and Race Conditions
6. What is a Race Condition?
7. The "Last Seat" Problem
8. Real-World Example: Double Booking
9. Why Simple Checks Don't Work
10. Lost Updates Problem

### Part 3: Locking Strategies
11. Pessimistic Locking (FOR UPDATE)
12. How FOR UPDATE Works in PostgreSQL
13. Lock Duration and Release
14. Optimistic Locking (Version Numbers)
15. When to Use Each Strategy

### Part 4: State Machines
16. What is a State Machine?
17. Booking State Diagram
18. Valid State Transitions
19. State Transition Validation
20. Invalid Transitions

### Part 5: Booking Service Architecture
21. File: `booking.py` (Model) - Structure
22. BookingStatus Enum
23. Composite Indexes
24. JSON Columns for Locations
25. Timestamps and Audit Fields

### Part 6: Booking Service Implementation
26. File: `booking_service.py` - Architecture
27. Create Booking with Locking
28. Approve Booking Flow
29. Reject Booking and Seat Release
30. Authorization Checks

### Part 7: API Routes and Endpoints
31. File: `bookings.py` - Endpoint Design
32. POST /bookings - Create Booking
33. POST /bookings/{id}/approve
34. POST /bookings/{id}/reject
35. GET /bookings/{id}

### Part 8: Transaction Isolation Levels
36. Read Uncommitted
37. Read Committed (PostgreSQL Default)
38. Repeatable Read
39. Serializable
40. Choosing the Right Level

### Part 9: Real-World Scenarios
41. Concurrent Booking Attempts
42. Transaction Rollback on Error
43. Deadlock Prevention
44. Inter-Service Consistency
45. Testing Concurrent Operations

### Part 10: Best Practices
46. Keep Transactions Short
47. Handle Errors Gracefully
48. Idempotency in APIs
49. Logging and Monitoring
50. Production Considerations

---

# Part 1: Database Transactions (ACID)

## 1. What are Database Transactions?

### The Concept

A **transaction** is a sequence of database operations that are treated as a single unit of work.

**Simple Analogy**: Transferring money between bank accounts
```
Step 1: Subtract $100 from Account A
Step 2: Add $100 to Account B

If Step 1 succeeds but Step 2 fails:
- $100 disappears! (Money lost)
- This is UNACCEPTABLE

Solution: Transaction
- Either BOTH steps succeed
- Or BOTH steps fail (rollback)
```

### Database Transactions

```python
async with db.begin():  # Start transaction
    # Step 1: Deduct from Account A
    await db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 'A'")

    # Step 2: Add to Account B
    await db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 'B'")

    # If we reach here without errors, transaction commits automatically
    # If any error occurs, transaction rolls back automatically
```

### Why Transactions for Bookings?

**Our Booking Process**:
```
Step 1: Check if seats available
Step 2: Decrease available seats
Step 3: Create booking record

What if crash happens after Step 2?
- Seats are gone
- But no booking exists
- Lost revenue!

With Transaction:
- All steps succeed together
- Or all steps rollback
- Consistency guaranteed
```

---

## 2. ACID Properties Explained

**ACID** = Atomicity, Consistency, Isolation, Durability

### A = Atomicity

**"All or Nothing"**

```python
# BAD: Without transaction
available_seats -= seats_requested  # Done
booking = create_booking()          # CRASH!
# Result: Seats decremented but no booking ❌

# GOOD: With transaction
async with db.begin():
    available_seats -= seats_requested
    booking = create_booking()
# Result: Both happen or neither ✅
```

**Real-World Analogy**:
- Ordering pizza: You don't pay unless pizza is delivered
- If delivery fails, payment is refunded
- Can't have half-paid, half-delivered state

### C = Consistency

**"Database rules are always followed"**

```python
# Constraint: seats_booked > 0
booking = Booking(seats_booked=-5)  # ❌ Violates constraint

# Transaction will REJECT this
# Database stays in valid state
```

**Rules enforced**:
- Foreign keys exist
- Check constraints satisfied
- Unique constraints not violated
- NOT NULL columns have values

### I = Isolation

**"Transactions don't interfere with each other"**

```
Transaction A: Book 2 seats on Ride X
Transaction B: Book 2 seats on Ride X
(Ride X has 3 seats total)

Without isolation:
- Both read "3 seats available"
- Both book 2 seats
- Result: 4 seats booked but only 3 exist! ❌

With isolation:
- Transaction A locks the ride
- Transaction B waits
- A books 2 seats (3 → 1 remaining)
- A commits and releases lock
- B sees 1 seat remaining
- B fails (needs 2, only 1 available) ✅
```

### D = Durability

**"Once committed, data persists"**

```python
async with db.begin():
    booking = create_booking()
    await db.commit()  # Committed!

# Even if server crashes NOW, booking is saved
# PostgreSQL writes to disk before commit returns
```

**How it works**:
- Database writes to transaction log (WAL - Write-Ahead Log)
- Log is on disk (survives crashes)
- Commit only returns after log is written
- If crash, database replays log on restart

---

## 3. Why Transactions Matter for Bookings

### Problem: Overbooking

**Scenario**: Ride has 1 seat left

```python
# WITHOUT TRANSACTION (BAD)
def create_booking():
    available = get_available_seats(ride_id)  # Returns 1
    if available >= requested:                 # True
        create_booking_record()                # Creates booking
        decrease_seats(ride_id)                # Decreases to 0

# What if TWO users do this SIMULTANEOUSLY?
User A: checks (1 seat) → creates booking → decreases (0 seats)
User B: checks (1 seat) → creates booking → decreases (-1 seats!) ❌

# Result: 2 bookings for 1 seat!
```

**Solution**: Transaction with lock
```python
# WITH TRANSACTION (GOOD)
async def create_booking():
    async with db.begin():
        # LOCK the ride row
        ride = await db.execute(
            "SELECT available_seats FROM rides WHERE id = :id FOR UPDATE",
            {"id": ride_id}
        )
        available = ride.scalar()

        if available >= requested:
            create_booking_record()
            decrease_seats(ride_id)
        # Lock released when transaction commits

# Now:
User A: locks ride → checks (1) → books → decreases (0) → commits
User B: WAITS for lock → checks (0) → fails ✅

# Only 1 booking succeeds!
```

---

## 4. Transaction Lifecycle

### The Five Stages

```
1. BEGIN
    ↓
2. EXECUTE (multiple SQL statements)
    ↓
3. VALIDATE (check constraints)
    ↓
4. COMMIT or ROLLBACK
    ↓
5. COMPLETE
```

### Our Implementation

```python
# booking_service.py

async def create_booking(self, user_id, booking_in):
    try:
        # 1. BEGIN
        async with self.db.begin():

            # 2. EXECUTE
            result = await self.db.execute(
                text("SELECT available_seats FROM rides WHERE id = :id FOR UPDATE"),
                {"id": booking_in.ride_id}
            )

            available_seats = result.scalar()

            # 3. VALIDATE (in our code)
            if available_seats < booking_in.seats_booked:
                raise HTTPException(status_code=400, detail="Not enough seats")

            # Update seats
            await self.db.execute(
                text("UPDATE rides SET available_seats = available_seats - :seats"),
                {"seats": booking_in.seats_booked}
            )

            # Create booking
            booking = Booking(...)
            self.db.add(booking)

            # 4. COMMIT (automatic when exiting 'async with' block successfully)

    except HTTPException:
        # 4. ROLLBACK (automatic if exception raised)
        raise

    # 5. COMPLETE
    return booking
```

### What Happens Under the Hood

```sql
-- 1. BEGIN
BEGIN;

-- 2. EXECUTE
SELECT available_seats FROM rides WHERE id = '123' FOR UPDATE;
UPDATE rides SET available_seats = 2 WHERE id = '123';
INSERT INTO bookings (...) VALUES (...);

-- 3. VALIDATE (database checks constraints)
-- Check: available_seats >= 0
-- Check: seats_booked > 0
-- Check: foreign keys exist

-- 4. COMMIT
COMMIT;
```

If any error in steps 2-3:
```sql
ROLLBACK;  -- Undo everything
```

---

## 5. Commit vs Rollback

### Commit

**When it happens**:
- All operations succeed
- All constraints satisfied
- No errors raised

**What it does**:
- Makes changes permanent
- Writes to disk (WAL)
- Releases locks
- Makes changes visible to other transactions

```python
async with db.begin():
    # ... operations ...
    # Exit normally → COMMIT automatically
```

### Rollback

**When it happens**:
- Exception raised
- Constraint violation
- Explicit rollback call
- Transaction timeout

**What it does**:
- Undoes ALL changes made in transaction
- Restores database to state before BEGIN
- Releases locks
- Nothing becomes visible to others

```python
async with db.begin():
    await db.execute("UPDATE rides SET available_seats = 0")

    # Oh no! Realized this is wrong
    raise Exception("Cancel this!")

    # Transaction ROLLS BACK
    # available_seats unchanged
```

---

# Part 2: Concurrency and Race Conditions

## 6. What is a Race Condition?

### The Concept

A **race condition** occurs when the correctness of a program depends on the timing or ordering of uncontrollable events.

**Simple Analogy**: Two people reaching for the last cookie
```
Person A: Sees cookie → Reaches for it → Grabs it
Person B: Sees cookie → Reaches for it → Grabs it

If timing overlaps:
- Both see cookie exists
- Both grab simultaneously
- Cookie breaks! (or conflict)
```

### In Programming

```python
# Shared variable
counter = 0

# Two threads/requests execute this simultaneously:
def increment():
    temp = counter      # Thread A: temp = 0
                        # Thread B: temp = 0
    temp = temp + 1     # Thread A: temp = 1
                        # Thread B: temp = 1
    counter = temp      # Thread A: counter = 1
                        # Thread B: counter = 1

# Expected: counter = 2
# Actual: counter = 1 ❌
```

**Why?**: Both threads read the same initial value before either writes

---

## 7. The "Last Seat" Problem

### Our Specific Race Condition

**Setup**: Ride has 1 seat available

**Two passengers** (A and B) try to book simultaneously:

```
TIME    Request A                   Request B
----    ---------                   ---------
t1      Check seats available       Check seats available
        Result: 1 ✓                 Result: 1 ✓

t2      Validate: 1 >= 1 ✓          Validate: 1 >= 1 ✓

t3      Create booking A            Create booking B

t4      Decrease seats: 1→0         Decrease seats: 0→-1 ❌

Result: 2 bookings, -1 seats available!
```

**Problem**: Both checked BEFORE either updated

---

## 8. Real-World Example: Double Booking

### Actual Code Without Locking

```python
# DANGEROUS CODE - Race Condition!
async def create_booking_UNSAFE(ride_id, seats_requested):
    # Step 1: Read available seats
    result = await db.execute(
        "SELECT available_seats FROM rides WHERE id = :id",
        {"id": ride_id}
    )
    available = result.scalar()  # Returns 1

    # Step 2: Check if enough
    if available >= seats_requested:  # True for both requests

        # Step 3: Create booking
        booking = Booking(...)
        db.add(booking)

        # Step 4: Update seats
        await db.execute(
            "UPDATE rides SET available_seats = available_seats - :seats",
            {"seats": seats_requested}
        )

        await db.commit()
```

### The Race in Detail

```
Request A                           Request B
=========                           =========
SELECT seats → 1
                                    SELECT seats → 1
Check: 1 >= 1 ✓
                                    Check: 1 >= 1 ✓
Create booking A
                                    Create booking B
UPDATE seats: 1-1=0
                                    UPDATE seats: 0-1=-1 ❌
Commit
                                    Commit

Database now has:
- Booking A (valid)
- Booking B (valid but shouldn't exist)
- available_seats = -1 (impossible!)
```

---

## 9. Why Simple Checks Don't Work

### Attempt 1: Check Before Update

```python
# Doesn't solve the problem!
available = get_available_seats()
if available >= requested:
    update_seats()  # Race can still occur here!
```

**Why fails**: Gap between check and update

### Attempt 2: Check in UPDATE Statement

```python
# Better, but still has issues
await db.execute(
    "UPDATE rides SET available_seats = available_seats - :seats "
    "WHERE id = :id AND available_seats >= :seats",
    {"seats": requested, "id": ride_id}
)

# Check rows affected
if rows_affected == 0:
    raise Exception("Not enough seats")
```

**Why fails**: Booking is created separately, can have mismatch

### Correct Solution: Transaction + Lock

```python
async with db.begin():
    # LOCK prevents other transactions from reading this row
    result = await db.execute(
        "SELECT available_seats FROM rides WHERE id = :id FOR UPDATE",
        {"id": ride_id}
    )
    available = result.scalar()

    if available >= requested:
        # Safe now! Lock held until commit
        create_booking()
        update_seats()
```

---

## 10. Lost Updates Problem

### What is a Lost Update?

When one transaction's update overwrites another's without seeing it.

**Example**: Two admins updating ride price

```
Admin A                         Admin B
=======                         =======
Read price: $10                 Read price: $10
Calculate: $10 + $5 = $15       Calculate: $10 - $2 = $8
Write: $15                      Write: $8

Final price: $8
Lost update: Admin A's +$5 change disappeared!
```

### In Our System

**Scenario**: Updating available seats

```python
# WITHOUT TRANSACTION
def update_seats():
    current = get_seats()        # Both read: 5
    new_value = current - 1      # A: 5-1=4, B: 5-1=4
    set_seats(new_value)         # Both write: 4

# Expected: 5-1-1 = 3
# Actual: 4 (one update lost!)
```

### Solution: Atomic Operations

```sql
-- Don't read-then-write
-- Do it in one operation
UPDATE rides
SET available_seats = available_seats - 1
WHERE id = :id;
```

**Why this works**: Database does read-modify-write atomically

---

# Part 3: Locking Strategies

## 11. Pessimistic Locking (FOR UPDATE)

### What is Pessimistic Locking?

**Philosophy**: "Assume conflicts will happen, prevent them upfront"

**How it works**: Lock the row, do your work, unlock

**Our Implementation**:
```python
async with db.begin():
    # SELECT ... FOR UPDATE
    result = await db.execute(
        text("SELECT available_seats FROM rides WHERE id = :id FOR UPDATE"),
        {"id": ride_id}
    )
```

### Why "Pessimistic"?

**Pessimistic** = Assumes the worst (conflicts likely)
- Locks preemptively
- Other transactions must wait
- Prevents all conflicts
- Slower (lock overhead)
- Safer (no conflicts)

**When to use**:
- High contention (many users booking same ride)
- Critical operations (money, seat availability)
- When conflict is expensive (refunds, customer service)

---

## 12. How FOR UPDATE Works in PostgreSQL

### The SQL

```sql
BEGIN;

SELECT available_seats, price_per_seat
FROM rides
WHERE id = '123e4567-e89b-12d3-a456-426614174000'
FOR UPDATE;

-- Other transactions trying to read this row will WAIT
-- Until this transaction COMMITs or ROLLBACKs

UPDATE rides SET available_seats = available_seats - 2 WHERE id = '...';
INSERT INTO bookings (...) VALUES (...);

COMMIT;  -- Releases lock
```

### Lock Behavior

**Transaction A** (holds lock):
```sql
SELECT * FROM rides WHERE id = '123' FOR UPDATE;
-- Lock acquired
-- Do work...
-- Still holding lock...
COMMIT;  -- Lock released
```

**Transaction B** (waits):
```sql
SELECT * FROM rides WHERE id = '123' FOR UPDATE;
-- BLOCKED! Waiting for Transaction A
-- ...waiting...
-- ...waiting...
-- Transaction A commits
-- Lock acquired! Continue
```

### Visual Timeline

```
Time    Transaction A           Transaction B
----    --------------          --------------
t1      BEGIN
t2      SELECT...FOR UPDATE
        (LOCK ACQUIRED)
t3                              BEGIN
t4                              SELECT...FOR UPDATE
                                (BLOCKED - waiting)
t5      UPDATE seats
        INSERT booking
t6      COMMIT
        (LOCK RELEASED)         (UNBLOCKED!)
t7                              SELECT complete
                                UPDATE seats
                                COMMIT
```

---

## 13. Lock Duration and Release

### How Long is Lock Held?

**From**: First `SELECT ... FOR UPDATE`
**Until**: Transaction ends (`COMMIT` or `ROLLBACK`)

```python
async with self.db.begin():  # Transaction starts

    # Lock acquired here ↓
    result = await self.db.execute(
        "SELECT * FROM rides WHERE id = :id FOR UPDATE"
    )

    # Lock still held...
    await self.db.execute("UPDATE rides ...")

    # Lock still held...
    booking = Booking(...)
    self.db.add(booking)

    # Lock still held...

# Transaction ends → Lock released automatically
```

### Timeout Handling

**Problem**: What if a transaction hangs?

```python
# Transaction A gets lock
SELECT * FROM rides WHERE id = '123' FOR UPDATE;
# ...then goes to sleep forever...

# Transaction B waits forever ❌
```

**Solution**: Lock timeout
```python
# PostgreSQL
SET lock_timeout = '10s';

# SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "command_timeout": 10  # 10 seconds
    }
)
```

**Better**: Statement timeout
```python
SET statement_timeout = '30s';

# Any query taking > 30s is cancelled
```

### Our Implementation

```python
# booking_service.py
async def create_booking(self, user_id, booking_in):
    try:
        async with self.db.begin():  # Start transaction

            # Acquire lock (blocks if another transaction has it)
            result = await self.db.execute(
                text("SELECT available_seats, price_per_seat "
                     "FROM rides WHERE id = :ride_id FOR UPDATE"),
                {"ride_id": booking_in.ride_id}
            )

            ride_row = result.fetchone()

            # Lock held during all these operations
            if not ride_row:
                raise HTTPException(status_code=404)

            available_seats = ride_row[0]

            if available_seats < booking_in.seats_booked:
                raise HTTPException(status_code=400)

            # Update
            await self.db.execute(
                text("UPDATE rides SET available_seats = available_seats - :seats "
                     "WHERE id = :ride_id"),
                {"seats": booking_in.seats_booked, "ride_id": booking_in.ride_id}
            )

            # Create booking
            booking_record = Booking(...)
            self.db.add(booking_record)

            # Lock released when exiting this block (COMMIT)

    except HTTPException:
        # Lock released on ROLLBACK
        raise
```

---

## 14. Optimistic Locking (Version Numbers)

### What is Optimistic Locking?

**Philosophy**: "Assume conflicts are rare, check at the end"

**How it works**: Add version number to table

```sql
CREATE TABLE rides (
    id UUID PRIMARY KEY,
    available_seats INT,
    version INT DEFAULT 0  -- Version number
);
```

### The Process

```python
# 1. Read with version
ride = await db.execute(
    "SELECT id, available_seats, version FROM rides WHERE id = :id"
)
current_version = ride.version  # e.g., version = 5

# 2. Do work (no lock held)
# User can take their time...

# 3. Update with version check
result = await db.execute(
    "UPDATE rides "
    "SET available_seats = :new_seats, version = version + 1 "
    "WHERE id = :id AND version = :current_version",
    {"new_seats": new_value, "id": ride_id, "current_version": current_version}
)

# 4. Check if update succeeded
if result.rowcount == 0:
    # Version changed! Someone else updated
    raise ConflictError("Ride was modified by another user")
```

### Optimistic vs Pessimistic

| Aspect | Pessimistic (FOR UPDATE) | Optimistic (Version) |
|--------|-------------------------|---------------------|
| **Philosophy** | Prevent conflicts | Detect conflicts |
| **Lock** | Yes, blocks others | No lock |
| **Performance** | Slower (blocking) | Faster (no blocking) |
| **Conflicts** | Prevented | Detected at commit |
| **Best for** | High contention | Low contention |
| **Complexity** | Simple | Need retry logic |

### When to Use Each

**Use Pessimistic (FOR UPDATE)** when:
- ✅ High contention expected (last seat scenario)
- ✅ Conflict is expensive to handle
- ✅ Short transactions
- ✅ Critical data (money, inventory)

**Use Optimistic (Version)** when:
- ✅ Low contention expected
- ✅ Long-running transactions
- ✅ Reads far outnumber writes
- ✅ Can retry easily

**Our choice**: Pessimistic
- Booking last seat = high contention
- Financial impact if wrong
- Transactions are short

---

## 15. When to Use Each Strategy

### Decision Tree

```
Do you expect frequent conflicts?
├─ Yes → Use Pessimistic Locking
│         (FOR UPDATE)
│
└─ No → Is retry acceptable?
         ├─ Yes → Use Optimistic Locking
         │         (Version numbers)
         │
         └─ No → Use Pessimistic Locking
                  (Safety first)
```

### Real-World Examples

#### **E-commerce Checkout** → Pessimistic
```
Last item in stock
Many users trying to buy
Conflict = lost sale
→ Use FOR UPDATE
```

#### **Blog Post Edit** → Optimistic
```
Two authors editing same post (rare)
Can show "Someone else edited, please merge"
Retry is acceptable
→ Use version numbers
```

#### **Bank Transfer** → Pessimistic
```
Money involved
Cannot have conflicts
Must be 100% accurate
→ Use FOR UPDATE
```

#### **Document Collaboration** → Optimistic
```
Multiple editors (like Google Docs)
Merge conflicts manually
Real-time sync
→ Use operational transforms (advanced optimistic)
```

### Our Implementation Choice

**Booking seats** → Pessimistic locking

**Reasons**:
1. High contention possible (popular rides, last seat)
2. Conflict = bad UX (user thinks they booked but didn't)
3. Financial impact (refunds, compensation)
4. Transactions are short (< 100ms)
5. Database can handle it

**Code**:
```python
# booking_service.py line 30-33
result = await self.db.execute(
    text("SELECT available_seats, price_per_seat "
         "FROM rides WHERE id = :ride_id FOR UPDATE"),
    {"ride_id": booking_in.ride_id}
)
```

---

# Part 4: State Machines

## 16. What is a State Machine?

### The Concept

A **state machine** is a model of computation with:
- **States**: Different conditions/modes
- **Transitions**: Rules for moving between states
- **Events**: Triggers that cause transitions

**Real-World Analogy**: Traffic Light
```
States: Red, Yellow, Green

Transitions:
- Red → Green (after timer)
- Green → Yellow (after timer)
- Yellow → Red (after timer)

Invalid transitions:
- Red → Yellow ❌
- Green → Red ❌
```

### Why State Machines?

**Benefits**:
1. **Clear rules**: Exactly which transitions are allowed
2. **Prevent bugs**: Can't get into invalid state
3. **Documentation**: States explain business logic
4. **Audit trail**: Track how booking progressed

**Example of bug prevented**:
```python
# Without state machine
booking.status = "completed"
# Oops! Was never approved first ❌

# With state machine
def complete(booking):
    if booking.status != "approved":
        raise InvalidTransition("Can only complete approved bookings")
    booking.status = "completed"
```

---

## 17. Booking State Diagram

### The States

```
┌─────────┐
│ PENDING │  Initial state after creation
└─────────┘
     │
     ├──────────────┬──────────────┐
     │              │              │
     ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌───────────┐
│ APPROVED │  │ REJECTED │  │ CANCELLED │
└──────────┘  └──────────┘  └───────────┘
     │              │              │
     │              │              │
     ▼              │              │
┌───────────┐       │              │
│ COMPLETED │       │              │
└───────────┘       │              │
     │              │              │
     └──────────────┴──────────────┘
              TERMINAL STATES
```

### State Descriptions

**PENDING**
- Just created by passenger
- Waiting for driver approval
- Seats are reserved (blocked)
- Can be: approved, rejected, or cancelled

**APPROVED**
- Driver accepted the booking
- Seats confirmed
- Ride will happen
- Can be: completed or cancelled

**REJECTED**
- Driver declined the booking
- Seats released back to ride
- **Terminal state** (no further transitions)

**CANCELLED**
- Cancelled by passenger or driver
- Seats released
- May trigger refund
- **Terminal state**

**COMPLETED**
- Ride finished
- Payment processed
- Ready for review
- **Terminal state**

---

## 18. Valid State Transitions

### Transition Table

| From State | To State | Triggered By | Condition |
|------------|----------|--------------|-----------|
| PENDING | APPROVED | Driver | None |
| PENDING | REJECTED | Driver | None |
| PENDING | CANCELLED | Passenger | Before approval |
| APPROVED | COMPLETED | Driver | After ride ends |
| APPROVED | CANCELLED | Passenger or Driver | Before ride starts |

### Detailed Transitions

#### **PENDING → APPROVED**
```python
# Who: Driver
# When: Reviews booking request and accepts
# What happens:
# - Booking status changes
# - Seats remain reserved
# - Passenger notified

await service.approve_booking(booking_id, driver_id)
```

#### **PENDING → REJECTED**
```python
# Who: Driver
# When: Reviews booking request and declines
# What happens:
# - Booking status changes
# - Seats released back to ride
# - Passenger notified

await service.reject_booking(booking_id, driver_id)
```

#### **PENDING → CANCELLED**
```python
# Who: Passenger
# When: Changes mind before driver approves
# What happens:
# - Booking cancelled
# - Seats released
# - Full refund (if paid)

await service.cancel_booking(booking_id, passenger_id)
```

#### **APPROVED → COMPLETED**
```python
# Who: Driver
# When: After ride finishes
# What happens:
# - Booking marked complete
# - Payment released to driver
# - Both can leave reviews

await service.complete_booking(booking_id, driver_id)
```

#### **APPROVED → CANCELLED**
```python
# Who: Passenger OR Driver
# When: Before ride starts
# What happens:
# - Booking cancelled
# - Seats released
# - Refund based on cancellation policy

await service.cancel_booking(booking_id, user_id)
```

---

## 19. State Transition Validation

### The Validation Function

```python
def validate_state_transition(current_state: BookingStatus, new_state: BookingStatus) -> bool:
    """
    Check if transition from current_state to new_state is allowed.
    """
    allowed_transitions = {
        BookingStatus.PENDING: [
            BookingStatus.APPROVED,
            BookingStatus.REJECTED,
            BookingStatus.CANCELLED
        ],
        BookingStatus.APPROVED: [
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED
        ],
        BookingStatus.COMPLETED: [],  # Terminal
        BookingStatus.REJECTED: [],   # Terminal
        BookingStatus.CANCELLED: []   # Terminal
    }

    return new_state in allowed_transitions.get(current_state, [])
```

### Usage in Service

```python
# booking_service.py

async def approve_booking(self, booking_id, driver_id):
    booking = await self.get_booking(booking_id)

    # Validate current state
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Booking is not pending (current: {booking.status})"
        )

    # ... perform approval ...
    booking.status = BookingStatus.APPROVED
```

### Benefits

**1. Prevents bugs**:
```python
# Without validation
booking.status = BookingStatus.COMPLETED
# Works even if booking is REJECTED! ❌

# With validation
if booking.status != BookingStatus.APPROVED:
    raise Exception("Can only complete approved bookings") ✅
```

**2. Clear error messages**:
```python
# User tries to approve already-rejected booking
# Response: "Booking is not pending (current: rejected)"
# User understands why it failed
```

**3. Business rule enforcement**:
```python
# Rule: "Only pending bookings can be approved"
# Enforced in code, not just documentation
```

---

## 20. Invalid Transitions

### Common Invalid Transitions

#### **COMPLETED → CANCELLED**
```
Why invalid: Ride already happened
Can't uncomplete a ride
Would need refund, but service provided
```

#### **REJECTED → APPROVED**
```
Why invalid: Driver already said no
Passenger should create new booking
Prevents flip-flopping
```

#### **CANCELLED → APPROVED**
```
Why invalid: Cancellation is final
Would complicate refund logic
Create new booking instead
```

#### **COMPLETED → APPROVED**
```
Why invalid: Can't go backwards
COMPLETED is terminal state
```

### Error Handling

```python
async def approve_booking(self, booking_id, driver_id):
    booking = await self.get_booking(booking_id)

    # Check current state
    if booking.status != BookingStatus.PENDING:

        # Provide helpful error based on current state
        if booking.status == BookingStatus.APPROVED:
            raise HTTPException(400, "Booking already approved")
        elif booking.status == BookingStatus.REJECTED:
            raise HTTPException(400, "Cannot approve rejected booking")
        elif booking.status == BookingStatus.CANCELLED:
            raise HTTPException(400, "Cannot approve cancelled booking")
        elif booking.status == BookingStatus.COMPLETED:
            raise HTTPException(400, "Cannot approve completed booking")

    # Proceed with approval...
```

---

# Part 5-10: Implementation Details

## 21-25. Booking Model (`booking.py`)

### Model Structure

```python
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationships
    ride_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Booking details
    seats_booked = Column(Integer, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Locations (JSON snapshots)
    pickup_location = Column(JSON, nullable=False)
    dropoff_location = Column(JSON, nullable=False)

    # Communication
    passenger_notes = Column(Text, nullable=True)
    driver_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Why JSON for Locations?

**Flexibility**:
```python
pickup_location = {
    "lat": 37.3352,
    "lng": -121.8811,
    "address": "San Jose State University",
    "notes": "Pick up at Tower Hall entrance"
}
```

**Snapshot**: Stores location at booking time, even if ride changes later

**No extra tables**: Don't need separate `booking_locations` table

---

## 26-30. Booking Service Implementation

### Create Booking with Locking (lines 18-79)

**Key points**:
1. **FOR UPDATE lock** prevents race conditions
2. **Check availability** while holding lock
3. **Immediate seat reservation** on PENDING
4. **Calculate total cost** from ride price
5. **Transaction ensures** all-or-nothing

### Approve Booking (lines 88-105)

**Flow**:
1. Get booking
2. Verify status is PENDING
3. Verify driver owns the ride
4. Change status to APPROVED
5. Keep seats reserved

### Reject Booking (lines 107-130)

**Flow**:
1. Get booking
2. Verify status is PENDING
3. Verify driver owns ride
4. **Release seats** back to ride
5. Change status to REJECTED

**Seat release**:
```python
await self.db.execute(
    text("UPDATE rides SET available_seats = available_seats + :seats"),
    {"seats": booking.seats_booked}
)
```

---

## 31-35. API Routes

### Endpoints Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | /bookings | Passenger | Create booking |
| GET | /bookings/{id} | Any | Get booking details |
| POST | /bookings/{id}/approve | Driver | Approve booking |
| POST | /bookings/{id}/reject | Driver | Reject booking |

### Current Implementation Note

**Authentication**: Currently using hardcoded UUIDs for testing
```python
async def get_current_user_id() -> UUID:
    return UUID("550e8400-e29b-41d4-a716-446655440099")
```

**Production**: Would use JWT token validation from Section 2

---

## 36-40. Transaction Isolation Levels

### PostgreSQL Default: Read Committed

**What it means**: You only see committed data

**Example**:
```
Transaction A                   Transaction B
=============                   =============
BEGIN                           BEGIN
SELECT price FROM rides
Result: $10
                                UPDATE rides SET price = $15
                                (not committed yet)
SELECT price FROM rides
Result: $10 (unchanged)
                                COMMIT
SELECT price FROM rides
Result: $15 (now sees it)
```

**Key**: Changes are invisible until committed

---

## 41-50. Real-World Scenarios & Best Practices

### Concurrent Booking Test

**Setup**: Ride with 1 seat

**Test**:
```python
import asyncio

async def book_seat(user_id):
    try:
        booking = await create_booking(user_id, ride_id, seats=1)
        return f"User {user_id}: SUCCESS"
    except:
        return f"User {user_id}: FAILED"

# Run 10 concurrent booking attempts
results = await asyncio.gather(*[
    book_seat(f"user_{i}") for i in range(10)
])

# Expected: 1 SUCCESS, 9 FAILED
assert results.count("SUCCESS") == 1
```

### Keep Transactions Short

**Good** ✅:
```python
async with db.begin():
    # Quick operations only
    result = await db.execute(...)
    booking = Booking(...)
    db.add(booking)
# Total: < 100ms
```

**Bad** ❌:
```python
async with db.begin():
    result = await db.execute(...)

    # Call external API (slow!)
    await send_email()  # 2 seconds

    booking = Booking(...)
    db.add(booking)
# Lock held for 2+ seconds!
```

### Production Considerations

**1. Monitoring**: Track transaction duration
**2. Alerting**: Alert if locks held > 1 second
**3. Retry logic**: Retry on deadlock (rare but possible)
**4. Logging**: Log all state transitions
**5. Idempotency**: Use idempotency keys for retries

---

## Summary

You've learned:
- **ACID properties** and why they matter
- **Race conditions** and the last-seat problem
- **Pessimistic locking** with FOR UPDATE
- **State machines** for booking workflow
- **Transaction management** in practice
- **Real-world patterns** for production systems

**Key takeaway**: Transactions + Locking = Correct concurrent operations

This foundation prepares you for complex distributed systems in later sections!
