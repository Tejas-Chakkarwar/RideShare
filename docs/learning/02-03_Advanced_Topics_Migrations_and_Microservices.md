# RideShare Academy: Module 2 - Advanced Topics
## Database Migrations, Microservices Communication, and Geospatial Features

This guide covers the advanced topics you've implemented in Section 2 and Section 3.

---

# Table of Contents

## Part 1: Database Migrations with Alembic
1. [What Are Database Migrations?](#part1-1)
2. [Why We Need Migrations](#part1-2)
3. [Alembic - The Migration Tool](#part1-3)
4. [Setting Up Alembic](#part1-4)
5. [Creating Your First Migration](#part1-5)
6. [Understanding Migration Files](#part1-6)
7. [Applying Migrations](#part1-7)
8. [Rolling Back Migrations](#part1-8)
9. [Auto-Generating Migrations](#part1-9)
10. [Migration Best Practices](#part1-10)
11. [Common Migration Scenarios](#part1-11)

## Part 2: Building the Ride Service
12. [Microservices Deep Dive](#part2-1)
13. [Service-to-Service Communication](#part2-2)
14. [HTTP Clients with HTTPX](#part2-3)
15. [Shared Database vs Separate Databases](#part2-4)
16. [The Ride Model Explained](#part2-5)
17. [Enums in SQLAlchemy](#part2-6)
18. [JSON Columns for Flexibility](#part2-7)
19. [Composite Indexes for Performance](#part2-8)

## Part 3: Geospatial Features
20. [Understanding Coordinates](#part3-1)
21. [The Haversine Formula](#part3-2)
22. [Proximity Search Implementation](#part3-3)
23. [Optimizing Geospatial Queries](#part3-4)

## Part 4: Advanced Pydantic
24. [Nested Schemas](#part4-1)
25. [Field Validators](#part4-2)
26. [Custom Validation Logic](#part4-3)
27. [Query Parameters with Pydantic](#part4-4)

## Part 5: Service Layer Pattern
28. [What is the Service Layer?](#part5-1)
29. [Why Separate Business Logic?](#part5-2)
30. [Service Layer in Practice](#part5-3)

## Part 6: User Registration Flow
31. [Complete Registration Implementation](#part6-1)
32. [Duplicate Email Handling](#part6-2)
33. [Database Refresh Pattern](#part6-3)

## Part 7: Docker Compose Advanced
34. [Service Dependencies](#part7-1)
35. [Container Communication](#part7-2)
36. [Volume Mounting for Development](#part7-3)

## Part 8: Real-World Scenarios
37. [Handling Concurrent Requests](#part8-1)
38. [Error Handling Across Services](#part8-2)
39. [Logging in Distributed Systems](#part8-3)

---

# PART 1: DATABASE MIGRATIONS WITH ALEMBIC

<a name="part1-1"></a>
## 1. What Are Database Migrations?

### The Problem Without Migrations

**Day 1:**
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String)
```

Your database has this table:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR
);
```

**Day 30:** You need to add a phone number field
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String)
    phone_number = Column(String)  # NEW!
```

**Problem:** Your code expects `phone_number`, but the database doesn't have it!

```python
user = User(email="john@sjsu.edu", phone_number="408-123-4567")
db.add(user)
# Error: column "phone_number" does not exist
```

### The Solution: Migrations

A **migration** is a script that changes your database schema:

```python
# Migration file: "add_phone_number.py"
def upgrade():
    op.add_column('users', Column('phone_number', String))

def downgrade():
    op.drop_column('users', 'phone_number')
```

Now you can:
1. **Upgrade:** Add the new column
2. **Downgrade:** Remove it if needed

---

<a name="part1-2"></a>
## 2. Why We Need Migrations

### Scenario 1: Team Development

**You:**
```python
# Add age field locally
class User(Base):
    age = Column(Integer)
```

**Your teammate:**
- Pulls your code
- Runs the app
- Error: "column age does not exist"

**With migrations:**
```bash
git pull
alembic upgrade head  # Apply all migrations
# Database now has age column!
```

### Scenario 2: Production Deployment

**Without migrations:**
```bash
# Deploy new code to production
# Users start getting errors
# You manually SSH into server
# Manually run SQL: ALTER TABLE users ADD COLUMN age INTEGER;
# Hope you didn't make a typo...
```

**With migrations:**
```bash
# Deploy new code
alembic upgrade head
# Database automatically updated!
```

### Scenario 3: Rollback

You deployed a buggy feature:
```bash
# Without migrations: Manually undo SQL changes (scary!)
# With migrations:
alembic downgrade -1  # Go back one migration
```

---

<a name="part1-3"></a>
## 3. Alembic - The Migration Tool

### What is Alembic?

Alembic is the de facto standard migration tool for SQLAlchemy.

**Analogy:**
- **Git** tracks changes to your code
- **Alembic** tracks changes to your database schema

### Alembic vs Alternatives

| Tool | Framework | Auto-Generate | Popularity |
|------|-----------|---------------|------------|
| **Alembic** | SQLAlchemy | ✅ Yes | ⭐⭐⭐⭐⭐ |
| Django Migrations | Django ORM | ✅ Yes | ⭐⭐⭐⭐⭐ |
| Flyway | Any (SQL files) | ❌ No | ⭐⭐⭐ |
| Liquibase | Any (XML/SQL) | ❌ No | ⭐⭐⭐ |

**For FastAPI + SQLAlchemy, Alembic is the best choice.**

---

<a name="part1-4"></a>
## 4. Setting Up Alembic

### Installation

Already in your `requirements.txt`:
```
alembic==1.12.1
```

### Initialization

```bash
cd backend/services/user-service
alembic init alembic
```

This creates:
```
user-service/
├── alembic/
│   ├── versions/          # Migration files go here
│   ├── env.py            # Migration environment config
│   └── script.py.mako    # Template for new migrations
├── alembic.ini           # Alembic configuration
```

### Configuration Files

**1. alembic.ini** (Main config):

From your file:
```ini
[alembic]
script_location = alembic
# ... other settings
sqlalchemy.url = driver://user:pass@localhost/dbname
```

**2. alembic/env.py** (Migration runtime):

From your file (lines 9-12):
```python
from app.core.config import settings
from app.db.base import Base
# Import all models so Base has them registered
from app.models import user  # noqa
```

**Why import models?**
- Alembic needs to know about your models
- It compares models to database schema
- Generates migrations based on differences

Line 24:
```python
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

**This overrides the dummy URL in alembic.ini with your actual database URL from settings.**

---

<a name="part1-5"></a>
## 5. Creating Your First Migration

### Manual Migration

```bash
alembic revision -m "create users table"
```

This creates:
```
alembic/versions/abc123_create_users_table.py
```

Inside:
```python
def upgrade():
    op.create_table(
        'users',
        Column('id', Integer, primary_key=True),
        Column('email', String, unique=True)
    )

def downgrade():
    op.drop_table('users')
```

### Auto-Generated Migration

**Better way:**

1. Define your models:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
```

2. Generate migration:
```bash
alembic revision --autogenerate -m "create users table"
```

Alembic:
- Looks at your models (via `Base.metadata`)
- Looks at your database
- Compares them
- **Automatically generates** the migration!

---

<a name="part1-6"></a>
## 6. Understanding Migration Files

Your migration file (`8ccc2b95210c_initial_migration.py`):

```python
"""Initial_migration

Revision ID: 8ccc2b95210c
Revises:
Create Date: 2025-12-27 03:14:00.387069
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8ccc2b95210c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    pass

def downgrade() -> None:
    """Downgrade schema."""
    pass
```

### Key Parts

**1. Revision ID:**
```python
revision: str = '8ccc2b95210c'
```
Unique identifier for this migration (like a Git commit hash).

**2. Down Revision:**
```python
down_revision: Union[str, Sequence[str], None] = None
```
Previous migration ID. `None` means this is the first migration.

**Migration chain:**
```
None → 8ccc2b95210c → abc123def456 → xyz789...
```

**3. upgrade():**
```python
def upgrade() -> None:
    pass
```
Apply the migration (create table, add column, etc.).

**4. downgrade():**
```python
def downgrade() -> None:
    pass
```
Reverse the migration (drop table, remove column, etc.).

### Why Empty?

Your migration is empty (`pass`) because:
1. Your tables already existed (created by `Base.metadata.create_all()`)
2. Alembic saw no difference between models and database
3. It created an empty migration as the "initial" state

**This is actually fine for your initial migration!**

---

<a name="part1-7"></a>
## 7. Applying Migrations

### Check Current State

```bash
alembic current
# Shows: (empty) or revision ID
```

### See Migration History

```bash
alembic history
# Shows all migrations
```

### Apply Migrations

**Upgrade to latest:**
```bash
alembic upgrade head
```

**Upgrade one step:**
```bash
alembic upgrade +1
```

**Upgrade to specific revision:**
```bash
alembic upgrade abc123
```

### What Happens Internally

1. Alembic connects to database
2. Checks table `alembic_version` (tracks current revision)
3. Finds migrations between current and target
4. Runs each `upgrade()` function in order
5. Updates `alembic_version` table

**The alembic_version table:**
```sql
SELECT * FROM alembic_version;
-- version_num
-- 8ccc2b95210c
```

---

<a name="part1-8"></a>
## 8. Rolling Back Migrations

### Downgrade One Step

```bash
alembic downgrade -1
```

### Downgrade to Specific Revision

```bash
alembic downgrade abc123
```

### Downgrade Everything

```bash
alembic downgrade base
```

**Warning:** This drops ALL tables!

### Example Rollback

**Migration 1:** Add phone_number column
```python
def upgrade():
    op.add_column('users', Column('phone_number', String))

def downgrade():
    op.drop_column('users', 'phone_number')
```

**Apply:**
```bash
alembic upgrade head
# Table now has phone_number
```

**Rollback:**
```bash
alembic downgrade -1
# phone_number column removed
```

---

<a name="part1-9"></a>
## 9. Auto-Generating Migrations

### The Magic Command

```bash
alembic revision --autogenerate -m "add phone number to users"
```

### What Alembic Detects

**Detects:**
- New tables
- Removed tables
- New columns
- Removed columns
- Changed column types
- Index changes

**Does NOT detect:**
- Column renames (sees as drop + add)
- Table renames (sees as drop + add)
- Changed column constraints (sometimes)

### Example

**1. Update your model:**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    phone_number = Column(String)  # NEW!
    age = Column(Integer)           # NEW!
```

**2. Generate migration:**
```bash
alembic revision --autogenerate -m "add phone and age"
```

**3. Alembic creates:**
```python
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('users', 'age')
    op.drop_column('users', 'phone_number')
```

**4. Review the migration** (always check autogenerated migrations!)

**5. Apply:**
```bash
alembic upgrade head
```

---

<a name="part1-10"></a>
## 10. Migration Best Practices

### 1. Always Review Autogenerated Migrations

```bash
alembic revision --autogenerate -m "description"
# Open the file and READ IT before applying!
```

**Why?**
- Alembic might miss some changes
- Might generate unsafe operations
- You might want to add data migrations

### 2. One Logical Change Per Migration

**Bad:**
```bash
alembic revision -m "add user phone, fix ride bug, update booking"
```

**Good:**
```bash
alembic revision -m "add phone number to users"
alembic revision -m "add index to rides departure_time"
alembic revision -m "add status to bookings"
```

**Why?** Easier to rollback specific changes.

### 3. Never Edit Applied Migrations

**Bad:**
```bash
# Migration already applied to production
alembic downgrade -1
# Edit migration file
alembic upgrade head
```

**Good:**
```bash
# Create NEW migration to fix the issue
alembic revision -m "fix phone number column type"
```

**Rule:** Treat applied migrations as immutable (like Git commits).

### 4. Always Have downgrade()

**Bad:**
```python
def upgrade():
    op.add_column('users', Column('phone', String))

def downgrade():
    pass  # No rollback!
```

**Good:**
```python
def upgrade():
    op.add_column('users', Column('phone', String))

def downgrade():
    op.drop_column('users', 'phone')
```

### 5. Test Migrations Locally

```bash
# Apply
alembic upgrade head

# Test app
python -m app.main

# Rollback
alembic downgrade -1

# Test app still works
python -m app.main

# Re-apply
alembic upgrade head
```

### 6. Backup Database Before Production Migrations

```bash
# Production deployment
pg_dump rideshare > backup.sql  # Backup first!
alembic upgrade head             # Then migrate
```

---

<a name="part1-11"></a>
## 11. Common Migration Scenarios

### Scenario 1: Add Column

```python
def upgrade():
    op.add_column('users', Column('bio', Text, nullable=True))

def downgrade():
    op.drop_column('users', 'bio')
```

### Scenario 2: Add Column with Default

```python
def upgrade():
    op.add_column('users', Column('is_verified', Boolean, default=False, nullable=False))

def downgrade():
    op.drop_column('users', 'is_verified')
```

### Scenario 3: Rename Column

```python
def upgrade():
    op.alter_column('users', 'full_name', new_column_name='name')

def downgrade():
    op.alter_column('users', 'name', new_column_name='full_name')
```

### Scenario 4: Change Column Type

```python
def upgrade():
    # Change phone from String to String(20)
    op.alter_column('users', 'phone_number', type_=String(20))

def downgrade():
    op.alter_column('users', 'phone_number', type_=String)
```

### Scenario 5: Add Index

```python
def upgrade():
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('ix_users_email', 'users')
```

### Scenario 6: Add Foreign Key

```python
def upgrade():
    op.add_column('rides', Column('driver_id', Integer, ForeignKey('users.id')))

def downgrade():
    op.drop_constraint('rides_driver_id_fkey', 'rides')
    op.drop_column('rides', 'driver_id')
```

### Scenario 7: Data Migration

```python
def upgrade():
    # Add column
    op.add_column('users', Column('status', String, nullable=True))

    # Migrate data
    conn = op.get_bind()
    conn.execute("UPDATE users SET status = 'active' WHERE is_active = true")
    conn.execute("UPDATE users SET status = 'inactive' WHERE is_active = false")

    # Make non-nullable
    op.alter_column('users', 'status', nullable=False)

    # Drop old column
    op.drop_column('users', 'is_active')

def downgrade():
    op.add_column('users', Column('is_active', Boolean))
    conn = op.get_bind()
    conn.execute("UPDATE users SET is_active = true WHERE status = 'active'")
    conn.execute("UPDATE users SET is_active = false WHERE status = 'inactive'")
    op.drop_column('users', 'status')
```

---

# PART 2: BUILDING THE RIDE SERVICE

<a name="part2-1"></a>
## 12. Microservices Deep Dive

### Your Architecture

```
┌──────────────────┐         ┌──────────────────┐
│  User Service    │         │  Ride Service    │
│  (Port 8001)     │         │  (Port 8002)     │
├──────────────────┤         ├──────────────────┤
│ - Register       │         │ - Create ride    │
│ - Login          │         │ - Search rides   │
│ - Profile        │         │ - Get ride       │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         └────────────┬───────────────┘
                      │
         ┌────────────▼─────────────┐
         │  PostgreSQL Database     │
         │  (Shared: rideshare)     │
         └──────────────────────────┘
```

### Why Separate Services?

**1. Independent Scaling**

Peak times:
- **Morning (8-10am):** Many ride searches → Scale ride-service
- **Evening (5-7pm):** Many ride searches → Scale ride-service
- **All day:** Steady login rate → Don't need to scale user-service

```bash
# Scale ride service only
docker-compose up --scale ride-service=3

# Now you have:
# - 1 user-service instance
# - 3 ride-service instances
```

**2. Independent Deployment**

```bash
# Update ride service logic (add new search feature)
git push
docker-compose up -d --build ride-service

# user-service keeps running (no downtime for users logging in)
```

**3. Team Organization**

- Team A: Works on user-service (authentication, profiles)
- Team B: Works on ride-service (rides, search)
- No merge conflicts!

**4. Technology Flexibility**

Future:
- User service: Python (current)
- Ride service: Go (for better performance)
- Booking service: Node.js (for real-time features)

---

<a name="part2-2"></a>
## 13. Service-to-Service Communication

### The Problem

Ride service needs to verify driver before creating ride:

```python
# In ride-service
async def create_ride(driver_id, ride_data):
    # Need to check: Does this user exist? Is driver verified?
    # But user data is in user-service! 🤔
```

### Solution 1: HTTP API Call

**From `ride-service/app/clients/user_client.py`:**

```python
class UserServiceClient:
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL  # "http://user-service:8000"

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v1/users/{user_id}"
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()
            return None
```

**Usage:**
```python
driver = await user_client.get_user(driver_id)
if not driver:
    raise ValueError("Driver not found")
```

**Flow:**
```
[Ride Service]
    ↓ HTTP GET http://user-service:8000/api/v1/users/123
[User Service]
    ↓ Query database
[User Service]
    ↑ Return {"id": 123, "email": "..."}
[Ride Service]
    ↑ Receives user data
```

### Solution 2: Shared Database (What You're Using)

**From `docker-compose.yml`:**

```yaml
user-service:
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare

ride-service:
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare
```

**Both services use the SAME database: `rideshare`**

**Tables:**
```
rideshare database:
├── users table (managed by user-service migrations)
└── rides table (managed by ride-service migrations)
```

**Pros:**
- Fast (no HTTP call overhead)
- Easier transactions (can join tables)
- Simpler for MVP

**Cons:**
- Tight coupling (both need same DB)
- Harder to scale (single DB bottleneck)
- Not "pure" microservices

**Your approach:** Hybrid
- Shared database for now (MVP simplicity)
- HTTP client ready for future (when you separate DBs)

---

<a name="part2-3"></a>
## 14. HTTP Clients with HTTPX

### What is HTTPX?

HTTPX is like `requests`, but with async support.

**Comparison:**

```python
# requests (synchronous)
import requests
response = requests.get("https://api.example.com")
data = response.json()

# httpx (asynchronous)
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
    data = response.json()
```

### Your Implementation

**From `user_client.py:18`:**

```python
async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}/api/v1/users/{user_id}"
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Error fetching user {user_id}: Status {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error connecting to user service: {e}")
        return None
```

### Key Features

**1. Timeout** (line 16):
```python
self.timeout = httpx.Timeout(10.0, connect=5.0)
```
- Total timeout: 10 seconds
- Connection timeout: 5 seconds

**Why?**
- User service might be down
- Don't wait forever
- Fail fast, return error to user

**2. Error Handling:**
```python
try:
    response = await client.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return None  # User doesn't exist
    else:
        logger.error(...)  # Other error
        return None
except Exception as e:
    logger.error(...)  # Network error
    return None
```

**3. Async Context Manager:**
```python
async with httpx.AsyncClient() as client:
    # client automatically closes after this block
```

### Using the Client

**In service layer** (`ride_service.py:20`):
```python
async def create_ride(self, ride_data, driver_id, db):
    # Verify driver exists
    driver = await user_client.get_user(driver_id)
    if not driver:
        raise ValueError("Driver not found")

    # Create ride
    ride = Ride(driver_id=driver_id, ...)
    db.add(ride)
    await db.commit()
    return ride
```

---

<a name="part2-4"></a>
## 15. Shared Database vs Separate Databases

### Your Current Setup: Shared Database

```yaml
# docker-compose.yml
services:
  postgres:
    environment:
      POSTGRES_DB: rideshare  # ONE database

  user-service:
    environment:
      DATABASE_URL: postgresql://...@postgres:5432/rideshare

  ride-service:
    environment:
      DATABASE_URL: postgresql://...@postgres:5432/rideshare
```

**Tables:**
```
rideshare
├── users (from user-service)
└── rides (from ride-service)
```

**Pros:**
- Simple setup
- Can use foreign keys: `rides.driver_id → users.id`
- Easy to join tables: `SELECT * FROM rides JOIN users ON rides.driver_id = users.id`
- Transactions work across services

**Cons:**
- Tight coupling (can't scale databases independently)
- Both services need database access
- Migrations can conflict

### Alternative: Separate Databases

```yaml
services:
  user-db:
    environment:
      POSTGRES_DB: users

  ride-db:
    environment:
      POSTGRES_DB: rides

  user-service:
    environment:
      DATABASE_URL: postgresql://...@user-db:5432/users

  ride-service:
    environment:
      DATABASE_URL: postgresql://...@ride-db:5432/rides
```

**Tables:**
```
users database:
└── users

rides database:
└── rides
```

**Pros:**
- True isolation
- Scale independently
- Can use different database types (Postgres for users, MongoDB for rides)

**Cons:**
- No foreign keys across databases
- No joins (must fetch separately)
- Distributed transactions are complex

**When to use each:**

| Shared DB | Separate DBs |
|-----------|--------------|
| MVP, small team | Large scale |
| Simple queries | Complex scaling needs |
| Fast development | True microservices |

**Your approach is perfect for MVP!**

---

<a name="part2-5"></a>
## 16. The Ride Model Explained

**From `models/ride.py`:**

```python
class Ride(Base):
    __tablename__ = "rides"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Driver
    driver_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Origin
    origin_address = Column(String(500), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)

    # Destination
    destination_address = Column(String(500), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)

    # Details
    departure_time = Column(DateTime(timezone=True), nullable=False, index=True)
    available_seats = Column(Integer, nullable=False)
    price_per_seat = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Vehicle
    vehicle_make = Column(String(100), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    vehicle_year = Column(Integer, nullable=False)
    vehicle_license_plate = Column(String(20), nullable=False)
    vehicle_color = Column(String(50), nullable=True)

    # Preferences (JSON)
    preferences = Column(JSON, nullable=True, default=dict)

    # Status
    status = Column(Enum(RideStatus), nullable=False, default=RideStatus.ACTIVE)

    # Recurring
    is_recurring = Column(Boolean, default=False)
    recurring_schedule = Column(JSON, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Field-by-Field Breakdown

**1. UUID Primary Key:**
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Why UUID instead of Integer?**

Integer (1, 2, 3...):
- Predictable
- Enumerable (can guess IDs: try 1, 2, 3...)
- Conflicts when merging databases

UUID (550e8400-e29b-41d4-a716-446655440000):
- Unpredictable (security)
- Globally unique
- No conflicts
- Can generate client-side

**2. Coordinates (Float):**
```python
origin_lat = Column(Float, nullable=False)
origin_lng = Column(Float, nullable=False)
```

**Why separate lat/lng instead of PostGIS POINT?**

PostGIS (geospatial extension):
```python
origin = Column(Geography('POINT'))
```
- More powerful (built-in distance, radius queries)
- Requires PostGIS extension
- More complex setup

Float (what you use):
- Simple
- No extensions needed
- Calculate distance in Python (Haversine)
- Good enough for MVP

**3. Numeric for Money:**
```python
price_per_seat = Column(Numeric(10, 2), nullable=False, default=0.00)
```

**Why Numeric instead of Float?**

Float:
```python
price = 10.1 + 20.2  # Might be 30.299999999 😱
```

Numeric (exact decimal):
```python
price = Decimal('10.1') + Decimal('20.2')  # Exactly 30.3 ✓
```

**Always use Numeric/Decimal for money!**

**4. DateTime with Timezone:**
```python
departure_time = Column(DateTime(timezone=True), nullable=False)
```

**timezone=True** stores UTC timestamps:
- User in California books ride for "2pm"
- Stored as "2024-12-20 22:00:00+00:00" (UTC)
- Displayed as "2pm PST" to California users
- Displayed as "11pm EST" to New York users

**timezone=False** (naive datetime):
- Stores "2024-12-20 14:00:00"
- What timezone? Who knows! 😱

**Always use timezone=True!**

---

<a name="part2-6"></a>
## 17. Enums in SQLAlchemy

**From `models/ride.py:11`:**

```python
class RideStatus(str, enum.Enum):
    """Enum for ride status"""
    ACTIVE = "active"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Ride(Base):
    status = Column(Enum(RideStatus), nullable=False, default=RideStatus.ACTIVE)
```

### Why Enums?

**Without Enum:**
```python
status = Column(String)

# In code
ride.status = "active"   # OK
ride.status = "activ"    # Typo! Bug! 😱
ride.status = "pending"  # Invalid! Bug! 😱
```

**With Enum:**
```python
status = Column(Enum(RideStatus))

# In code
ride.status = RideStatus.ACTIVE     # ✓
ride.status = RideStatus.CANCELLED  # ✓
ride.status = "activ"               # Type error! IDE catches it!
ride.status = "pending"             # Error! Not in enum!
```

### How It Works in Database

**Generated SQL:**
```sql
CREATE TYPE ridestatus AS ENUM ('active', 'full', 'completed', 'cancelled');

CREATE TABLE rides (
    id UUID PRIMARY KEY,
    status ridestatus NOT NULL DEFAULT 'active'
);
```

**Queries:**
```python
# Find all active rides
query = select(Ride).where(Ride.status == RideStatus.ACTIVE)

# Change status
ride.status = RideStatus.COMPLETED
```

**In JSON response:**
```json
{
  "id": "...",
  "status": "active"  // String value
}
```

---

<a name="part2-7"></a>
## 18. JSON Columns for Flexibility

**From `models/ride.py:74`:**

```python
preferences = Column(JSON, nullable=True, default=dict)
recurring_schedule = Column(JSON, nullable=True)
```

### Why JSON Columns?

**Problem:** Preferences might vary:

User 1 preferences:
```json
{
  "music": "no",
  "smoking": "no",
  "pets": "yes"
}
```

User 2 preferences:
```json
{
  "music": "yes",
  "conversation": "no",
  "temperature": "cool"
}
```

**Different fields for each user!**

**Solution 1: Create columns for every possible preference (bad):**
```python
music_preference = Column(String)
smoking_preference = Column(String)
pets_preference = Column(String)
conversation_preference = Column(String)
temperature_preference = Column(String)
# ... 100 more columns?!
```

**Solution 2: JSON column (good):**
```python
preferences = Column(JSON)
```

Store anything:
```json
{
  "any": "structure",
  "nested": {
    "data": ["works", "fine"]
  }
}
```

### Using JSON Columns

**Create:**
```python
ride = Ride(
    preferences={
        "music": "no",
        "smoking": "no",
        "pets": "yes"
    }
)
db.add(ride)
await db.commit()
```

**Read:**
```python
ride = await db.get(Ride, ride_id)
print(ride.preferences["music"])  # "no"
```

**Query (PostgreSQL specific):**
```python
# Find rides where music is allowed
query = select(Ride).where(Ride.preferences['music'].astext == 'yes')
```

### Pros and Cons

**Pros:**
- Flexible schema
- No migrations for new preferences
- Easy to store complex data

**Cons:**
- Can't index JSON fields easily
- Harder to query
- No type validation in database

**When to use:**
- Flexible, user-defined data
- Configuration data
- Data that changes frequently

**When NOT to use:**
- Critical data (use proper columns)
- Data you frequently query
- Data that needs indexes

---

<a name="part2-8"></a>
## 19. Composite Indexes for Performance

**From `models/ride.py:91`:**

```python
__table_args__ = (
    Index('ix_rides_driver_id', 'driver_id'),
    Index('ix_rides_departure_time', 'departure_time'),
    Index('ix_rides_status', 'status'),
    Index('ix_rides_origin_coords', 'origin_lat', 'origin_lng'),
    Index('ix_rides_destination_coords', 'destination_lat', 'destination_lng'),
)
```

### What Are Indexes?

**Book analogy:**

Without index:
- Find "Chapter about Dogs" → Read entire book page by page 😴

With index (table of contents):
- Look up "Dogs" → "Page 47" → Jump directly ⚡

**Database:**

Without index:
```sql
SELECT * FROM rides WHERE driver_id = 123;
-- Scans ALL rows (10,000 rides) → 500ms
```

With index:
```sql
CREATE INDEX ix_rides_driver_id ON rides(driver_id);
SELECT * FROM rides WHERE driver_id = 123;
-- Uses index → Finds rows directly → 5ms
```

### Single vs Composite Indexes

**Single column index:**
```python
Index('ix_rides_driver_id', 'driver_id')
```

Good for:
```sql
SELECT * FROM rides WHERE driver_id = 123;
```

**Composite index (multiple columns):**
```python
Index('ix_rides_origin_coords', 'origin_lat', 'origin_lng')
```

Good for:
```sql
SELECT * FROM rides WHERE origin_lat = 37.33 AND origin_lng = -121.88;
```

**Why composite for coordinates?**

Separate indexes:
```python
Index('ix_rides_origin_lat', 'origin_lat')
Index('ix_rides_origin_lng', 'origin_lng')
```

Query:
```sql
WHERE origin_lat = 37.33 AND origin_lng = -121.88
-- Database uses ONE index, scans results with other condition
-- Slower!
```

Composite index:
```python
Index('ix_rides_origin_coords', 'origin_lat', 'origin_lng')
```

Query:
```sql
WHERE origin_lat = 37.33 AND origin_lng = -121.88
-- Database uses BOTH columns in index
-- Faster! ⚡
```

### Index Performance

**Example: 1 million rides**

| Query | No Index | With Index |
|-------|----------|------------|
| Find by driver_id | 800ms | 5ms |
| Find by status | 600ms | 3ms |
| Find by departure_time | 900ms | 4ms |
| Find by coordinates | 1200ms | 10ms |

**160x faster!**

### When to Add Indexes

**Add index if:**
- Column used in WHERE clauses
- Column used in ORDER BY
- Column used in JOIN conditions
- Slow queries (check with EXPLAIN)

**Don't over-index:**
- Indexes slow down writes (INSERT, UPDATE)
- Indexes take disk space
- Too many indexes → database confusion

**Rule of thumb:**
- Index columns you query often
- Don't index columns you rarely query

---

# PART 3: GEOSPATIAL FEATURES

<a name="part3-1"></a>
## 20. Understanding Coordinates

### What Are Coordinates?

**Latitude + Longitude** pinpoint any location on Earth.

**Latitude (North/South):**
- Equator: 0°
- North Pole: 90°
- South Pole: -90°
- San Jose, CA: 37.33°

**Longitude (East/West):**
- Prime Meridian (Greenwich, UK): 0°
- East: 0° to 180°
- West: 0° to -180°
- San Jose, CA: -121.88°

**Your model:**
```python
origin_lat = Column(Float, nullable=False)  # 37.33
origin_lng = Column(Float, nullable=False)  # -121.88
```

### Real Examples

```python
# San Jose State University
lat = 37.3352
lng = -121.8811

# San Francisco
lat = 37.7749
lng = -122.4194

# Santa Cruz
lat = 36.9741
lng = -122.0308
```

### Accuracy

- **1 decimal place** (1.0): ~11 km
- **2 decimal places** (1.00): ~1.1 km
- **3 decimal places** (1.000): ~110 m
- **4 decimal places** (1.0000): ~11 m (your precision with Float)
- **6 decimal places** (1.000000): ~11 cm

**Float gives you ~11 meter accuracy** (perfect for ride sharing!)

---

<a name="part3-2"></a>
## 21. The Haversine Formula

### The Problem

**How far is SJSU from San Francisco?**

Simple math (wrong):
```python
lat_diff = 37.7749 - 37.3352  # 0.4397
lng_diff = -122.4194 - (-121.8811)  # -0.5383

distance = sqrt(lat_diff**2 + lng_diff**2)  # 0.699

# 0.699 degrees ≈ 78 km
# But actual distance is ~80 km (close, but not accurate!)
```

**Why wrong?**
- Earth is a sphere, not flat
- Degrees are not equal distances (1° latitude ≠ 1° longitude at different latitudes)

### The Solution: Haversine Formula

**From `utils/geo.py:3`:**

```python
def haversine_distance(lat1, lng1, lat2, lng2):
    """
    Calculate great circle distance between two points.
    Returns: Distance in kilometers
    """
    R = 6371.0  # Earth radius in kilometers

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    # Haversine formula
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
```

### How It Works

**1. Convert degrees to radians:**
```python
lat1_rad = math.radians(lat1)
# 37.3352° → 0.6516 radians
```

**Why?** Math functions (sin, cos) work with radians.

**2. Calculate differences:**
```python
dlat = lat2_rad - lat1_rad
dlng = lng2_rad - lng1_rad
```

**3. Haversine formula:**
```python
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlng/2)
```

This accounts for:
- Earth's curvature
- Longitude lines converging at poles

**4. Calculate arc length:**
```python
c = 2 × atan2(√a, √(1-a))
distance = R × c  # R = Earth radius
```

### Example

```python
# SJSU to San Francisco
sjsu_lat, sjsu_lng = 37.3352, -121.8811
sf_lat, sf_lng = 37.7749, -122.4194

distance = haversine_distance(sjsu_lat, sjsu_lng, sf_lat, sf_lng)
print(distance)  # ~79.8 km ✓ (accurate!)
```

### Accuracy

Haversine assumes:
- Earth is a perfect sphere
- Radius: 6371 km

**Actual Earth:**
- Slightly ellipsoid (flattened at poles)
- More complex formulas exist (Vincenty)

**Haversine accuracy:** ~0.5% error
- For ride sharing: Perfect!
- For GPS navigation: Usually sufficient
- For surveying: Use Vincenty

---

<a name="part3-3"></a>
## 22. Proximity Search Implementation

### The Goal

User searches for rides:
- User location: SJSU (37.3352, -121.8811)
- Search radius: 5 km
- Find all rides starting within 5 km

### Your Implementation

**From `services/ride_service.py:59`:**

```python
async def search_rides(self, params: RideSearchParams, db: AsyncSession):
    # 1. Get all active rides
    query = select(Ride).where(
        Ride.status == RideStatus.ACTIVE,
        Ride.available_seats >= params.min_seats,
        Ride.departure_time >= datetime.now(timezone.utc)
    )
    result = await db.execute(query)
    rides = result.scalars().all()

    # 2. Filter by proximity
    filtered_rides = []
    if params.origin_lat and params.origin_lng:
        for ride in rides:
            dist = haversine_distance(
                params.origin_lat, params.origin_lng,
                ride.origin_lat, ride.origin_lng
            )
            if dist <= params.proximity_km:
                filtered_rides.append(ride)
        return filtered_rides

    return rides
```

### Step-by-Step

**1. Database query (filter obvious criteria):**
```python
query = select(Ride).where(
    Ride.status == RideStatus.ACTIVE,  # Only active rides
    Ride.available_seats >= params.min_seats,  # Enough seats
    Ride.departure_time >= datetime.now()  # Future rides only
)
```

**This filters 1,000,000 rides → 10,000 rides**

**2. In-memory proximity filter:**
```python
for ride in rides:
    dist = haversine_distance(
        params.origin_lat, params.origin_lng,
        ride.origin_lat, ride.origin_lng
    )
    if dist <= params.proximity_km:
        filtered_rides.append(ride)
```

**This filters 10,000 rides → 50 rides within 5km**

### Performance

**Problem:** Calculating distance for 10,000 rides in Python is slow!

**For MVP:** Good enough
- 10,000 iterations × 0.001ms each = 10ms ✓

**For scale (1 million rides):**
- 1,000,000 iterations × 0.001ms = 1000ms ❌ Too slow!

**Solution (future optimization):**
Use bounding box pre-filter in SQL:

```python
# Calculate bounding box (lat/lng min/max)
# 5km radius ≈ 0.045° latitude
lat_min = params.origin_lat - 0.045
lat_max = params.origin_lat + 0.045
lng_min = params.origin_lng - 0.055  # Adjust for latitude
lng_max = params.origin_lng + 0.055

# SQL filter (very fast with index!)
query = select(Ride).where(
    Ride.origin_lat.between(lat_min, lat_max),
    Ride.origin_lng.between(lng_min, lng_max)
)
# This filters 1,000,000 → 100 rides in SQL

# Then calculate exact distance for those 100
for ride in rides:
    dist = haversine_distance(...)
```

**Result: 1000ms → 10ms** (100x faster!)

---

<a name="part3-4"></a>
## 23. Optimizing Geospatial Queries

### Current Approach (MVP)

```python
# 1. Fetch ALL active rides from database
rides = await db.execute(select(Ride).where(Ride.status == RideStatus.ACTIVE))

# 2. Calculate distance for each ride
for ride in rides:
    distance = haversine_distance(user_lat, user_lng, ride.origin_lat, ride.origin_lng)
    if distance <= 5:
        results.append(ride)
```

**Performance:** 10,000 rides = ~10ms (acceptable)

### Optimization 1: Bounding Box

**Idea:** Pre-filter in SQL before calculating exact distance

```python
# Calculate bounding box
# For 5km radius at latitude 37°:
# 1° latitude ≈ 111 km
# 1° longitude ≈ 85 km (varies with latitude)

lat_delta = 5 / 111  # 0.045°
lng_delta = 5 / (111 * math.cos(math.radians(user_lat)))  # 0.055°

lat_min = user_lat - lat_delta
lat_max = user_lat + lat_delta
lng_min = user_lng - lng_delta
lng_max = user_lng + lng_delta

# SQL query with bounding box
query = select(Ride).where(
    Ride.status == RideStatus.ACTIVE,
    Ride.origin_lat.between(lat_min, lat_max),
    Ride.origin_lng.between(lng_min, lng_max)
)
```

**Visual:**
```
         lng_min              lng_max
           │                    │
lat_max ───┌────────────────────┐
           │                    │
           │   [5km radius]     │
user_lat ──│─────────●──────────│
           │                    │
           │                    │
lat_min ───└────────────────────┘
```

**Performance improvement:**
- Without box: Scan 10,000 rides
- With box: Scan ~100 rides (100x fewer!)
- Then calculate exact distance for those 100

### Optimization 2: Composite Index

```python
# In models/ride.py
Index('ix_rides_origin_coords', 'origin_lat', 'origin_lng')
```

Makes bounding box query very fast:
```sql
WHERE origin_lat BETWEEN 37.29 AND 37.38
  AND origin_lng BETWEEN -121.93 AND -121.83
-- Uses index → instant! ⚡
```

### Optimization 3: PostGIS (Future)

**Install PostGIS extension:**
```sql
CREATE EXTENSION postgis;
```

**Change model:**
```python
from geoalchemy2 import Geography

class Ride(Base):
    origin = Column(Geography('POINT'))
    # Instead of separate lat/lng
```

**Query:**
```python
from geoalchemy2 import functions as geo_func

query = select(Ride).where(
    geo_func.ST_DWithin(
        Ride.origin,
        f'SRID=4326;POINT({user_lng} {user_lat})',
        5000  # 5km in meters
    )
)
# Database calculates distance natively!
```

**Performance:**
- Uses spatial indexes (R-tree)
- Much faster than Haversine in Python
- Can do complex geospatial queries

**When to use:**
- Large scale (millions of rides)
- Complex geo queries (routes, polygons)
- Need maximum performance

**Your approach (Float + Haversine):** Perfect for MVP!

---

# PART 4: ADVANCED PYDANTIC

<a name="part4-1"></a>
## 24. Nested Schemas

**From `schemas/ride.py:7`:**

```python
class LocationSchema(BaseModel):
    address: str = Field(..., min_length=5, max_length=500)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class VehicleSchema(BaseModel):
    make: str = Field(..., min_length=2, max_length=100)
    model: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=1900, le=2030)
    license_plate: str = Field(..., min_length=2, max_length=20)
    color: Optional[str] = Field(None, max_length=50)

class RideCreate(BaseModel):
    origin: LocationSchema  # Nested!
    destination: LocationSchema  # Nested!
    vehicle: VehicleSchema  # Nested!
    departure_time: datetime
    available_seats: int
```

### Why Nested Schemas?

**Without nesting (flat):**
```python
class RideCreate(BaseModel):
    origin_address: str
    origin_lat: float
    origin_lng: float
    destination_address: str
    destination_lat: float
    destination_lng: float
    vehicle_make: str
    vehicle_model: str
    # ... 15 more fields!
```

**JSON:**
```json
{
  "origin_address": "...",
  "origin_lat": 37.33,
  "origin_lng": -121.88,
  "destination_address": "...",
  "destination_lat": 37.77,
  "destination_lng": -122.41,
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry"
}
```

**Problems:**
- Flat structure (hard to organize)
- Repetitive validation
- Unclear grouping

**With nesting (structured):**
```python
class RideCreate(BaseModel):
    origin: LocationSchema
    destination: LocationSchema
    vehicle: VehicleSchema
```

**JSON:**
```json
{
  "origin": {
    "address": "...",
    "lat": 37.33,
    "lng": -121.88
  },
  "destination": {
    "address": "...",
    "lat": 37.77,
    "lng": -122.41
  },
  "vehicle": {
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "license_plate": "7ABC123"
  }
}
```

**Benefits:**
- Clear structure
- Reusable schemas (LocationSchema used twice!)
- Validation grouped logically

### Validation

```python
origin: LocationSchema
```

Pydantic validates:
```json
{
  "origin": {
    "address": "Hi",  // Too short! Min 5 chars
    "lat": 200,       // Invalid! Max 90
    "lng": -121.88
  }
}
```

**Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "origin", "address"],
      "msg": "ensure this value has at least 5 characters",
      "type": "value_error.any_str.min_length"
    },
    {
      "loc": ["body", "origin", "lat"],
      "msg": "ensure this value is less than or equal to 90",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**Notice:** Error path shows nesting: `["body", "origin", "lat"]`

---

<a name="part4-2"></a>
## 25. Field Validators

**From `schemas/ride.py:32`:**

```python
class RideBase(BaseModel):
    departure_time: datetime

    @field_validator('departure_time')
    @classmethod
    def validate_departure_time(cls, v: datetime) -> datetime:
        """Ensure departure time is at least 1 hour in the future"""
        from datetime import timezone, timedelta

        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        min_time = now + timedelta(hours=1)

        # Commented out for debugging, but you can uncomment:
        # if v < min_time:
        #     raise ValueError('Departure time must be at least 1 hour in the future')

        return v
```

### What Are Field Validators?

Custom validation logic for specific fields.

**Without validator:**
```python
departure_time: datetime  # Any datetime is valid
```

**User can create ride for yesterday:**
```json
{
  "departure_time": "2020-01-01T10:00:00Z"  // In the past!
}
```

**With validator:**
```python
@field_validator('departure_time')
def validate_departure_time(cls, v):
    if v < datetime.now() + timedelta(hours=1):
        raise ValueError('Must be at least 1 hour in the future')
    return v
```

**Now past dates are rejected:**
```json
{
  "departure_time": "2020-01-01T10:00:00Z"
}
```

**Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "departure_time"],
      "msg": "Departure time must be at least 1 hour in the future",
      "type": "value_error"
    }
  ]
}
```

### Multiple Validators

```python
class RideCreate(BaseModel):
    price_per_seat: Decimal
    available_seats: int

    @field_validator('price_per_seat')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        if v > 100:
            raise ValueError('Price too high (max $100)')
        return v

    @field_validator('available_seats')
    def validate_seats(cls, v):
        if v < 1:
            raise ValueError('Must have at least 1 seat')
        if v > 7:
            raise ValueError('Cannot exceed 7 seats')
        return v
```

### Validator with Dependencies

```python
from pydantic import model_validator

class RideCreate(BaseModel):
    departure_time: datetime
    available_seats: int
    price_per_seat: Decimal

    @model_validator(mode='after')
    def validate_total_price(self):
        total = self.available_seats * self.price_per_seat
        if total > 500:
            raise ValueError(f'Total price (${total}) exceeds maximum ($500)')
        return self
```

**This validator:**
- Runs AFTER all fields are validated
- Can access multiple fields
- Validates relationships between fields

---

<a name="part4-3"></a>
## 26. Custom Validation Logic

### Example: Coordinate Validation

```python
class LocationSchema(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

    @field_validator('lat')
    @classmethod
    def validate_latitude(cls, v):
        # Basic validation already done by Field(ge=-90, le=90)
        # Additional custom logic:
        if abs(v) < 0.001:
            raise ValueError('Coordinates too close to 0,0 (likely invalid)')
        return v
```

### Example: Email Domain Validation

```python
class UserCreate(BaseModel):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_sjsu_email(cls, v):
        if not v.endswith('@sjsu.edu'):
            raise ValueError('Must use SJSU email (@sjsu.edu)')
        return v.lower()  # Normalize to lowercase
```

### Example: Phone Number Formatting

```python
class UserCreate(BaseModel):
    phone_number: str

    @field_validator('phone_number')
    @classmethod
    def format_phone(cls, v):
        # Remove all non-digits
        digits = ''.join(c for c in v if c.isdigit())

        # Validate length
        if len(digits) != 10:
            raise ValueError('Phone must be 10 digits')

        # Format as (408) 123-4567
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
```

**Input:** `"4081234567"` or `"408-123-4567"` or `"(408) 123-4567"`
**Output:** `"(408) 123-4567"` (normalized!)

---

<a name="part4-4"></a>
## 27. Query Parameters with Pydantic

**From `schemas/ride.py:82`:**

```python
class RideSearchParams(BaseModel):
    origin_lat: Optional[float] = Field(None, ge=-90, le=90)
    origin_lng: Optional[float] = Field(None, ge=-180, le=180)
    destination_lat: Optional[float] = Field(None, ge=-90, le=90)
    destination_lng: Optional[float] = Field(None, ge=-180, le=180)
    departure_date: Optional[str] = None
    min_seats: int = Field(1, ge=1, le=7)
    proximity_km: float = Field(5.0, ge=0.1, le=50.0)
```

### Usage in Route

**From `routes/rides.py:30`:**

```python
@router.get("/", response_model=List[RideResponse])
async def search_rides(
    search_params: RideSearchParams = Depends(),  # ← Magic!
    db: AsyncSession = Depends(get_db)
):
    return await ride_service.search_rides(search_params, db)
```

### How It Works

**URL:**
```
GET /api/v1/rides?origin_lat=37.33&origin_lng=-121.88&proximity_km=5&min_seats=2
```

**FastAPI automatically:**
1. Extracts query parameters
2. Creates `RideSearchParams` instance
3. Validates each field
4. Passes to your function

**Equivalent manual code:**
```python
@router.get("/")
async def search_rides(
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
    proximity_km: float = 5.0,
    min_seats: int = 1,
    db: AsyncSession = Depends(get_db)
):
    # Manually validate
    if origin_lat and (origin_lat < -90 or origin_lat > 90):
        raise HTTPException(400, "Invalid latitude")
    # ... repeat for all fields

    # Create params object
    params = RideSearchParams(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        proximity_km=proximity_km,
        min_seats=min_seats
    )

    return await ride_service.search_rides(params, db)
```

**Pydantic does all this automatically!**

### Default Values

```python
proximity_km: float = Field(5.0, ge=0.1, le=50.0)
```

**URL without parameter:**
```
GET /api/v1/rides?origin_lat=37.33
```

**Result:** `proximity_km = 5.0` (default)

### Validation

**Invalid query:**
```
GET /api/v1/rides?proximity_km=100
```

**Error:**
```json
{
  "detail": [
    {
      "loc": ["query", "proximity_km"],
      "msg": "ensure this value is less than or equal to 50.0",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

# PART 5: SERVICE LAYER PATTERN

<a name="part5-1"></a>
## 28. What is the Service Layer?

### The Problem

**Without service layer** (putting logic in routes):

```python
# routes/rides.py
@router.post("/")
async def create_ride(ride_in: RideCreate, db: AsyncSession = Depends(get_db)):
    # Verify driver
    driver_query = select(User).where(User.id == driver_id)
    driver_result = await db.execute(driver_query)
    driver = driver_result.scalar_one_or_none()
    if not driver:
        raise HTTPException(404, "Driver not found")

    # Create ride
    ride = Ride(
        driver_id=driver_id,
        origin_address=ride_in.origin.address,
        origin_lat=ride_in.origin.lat,
        # ... 20 more fields
    )
    db.add(ride)
    await db.commit()
    await db.refresh(ride)

    # Send notification
    # ... 50 more lines

    return ride
```

**Problems:**
- Route handler is 100+ lines
- Business logic mixed with HTTP logic
- Hard to test (need to mock HTTP request)
- Can't reuse logic (what if CLI needs same logic?)

### The Solution: Service Layer

**routes/rides.py** (thin layer):
```python
@router.post("/")
async def create_ride(
    ride_in: RideCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await ride_service.create_ride(ride_in, current_user_id, db)
```

**services/ride_service.py** (business logic):
```python
class RideService:
    async def create_ride(self, ride_data, driver_id, db):
        # All business logic here
        driver = await user_client.get_user(driver_id)
        if not driver:
            raise ValueError("Driver not found")

        ride = Ride(...)
        db.add(ride)
        await db.commit()
        return ride
```

**Benefits:**
- Route handler: 5 lines (just HTTP stuff)
- Service layer: Business logic
- Easy to test service layer separately
- Reusable from CLI, background jobs, etc.

---

<a name="part5-2"></a>
## 29. Why Separate Business Logic?

### Testing

**Without service layer:**
```python
# Have to test via HTTP
def test_create_ride():
    response = client.post("/rides", json={...})
    assert response.status_code == 201
```

**With service layer:**
```python
# Can test business logic directly
async def test_create_ride_logic():
    ride = await ride_service.create_ride(ride_data, driver_id, db)
    assert ride.driver_id == driver_id
    assert ride.status == RideStatus.ACTIVE
```

### Reusability

**Scenario: Add CLI command to create ride**

Without service layer:
```python
# Duplicate logic from route handler 😭
async def cli_create_ride():
    # Copy-paste 100 lines from routes/rides.py
    ...
```

With service layer:
```python
# Reuse!
async def cli_create_ride():
    await ride_service.create_ride(ride_data, driver_id, db)
```

### Changing Implementation

**Scenario: Switch from HTTP client to message queue**

Without service layer:
```python
# Have to change routes/rides.py
# If logic is in 5 different routes, change all 5!
```

With service layer:
```python
# Change only ride_service.py
class RideService:
    async def create_ride(self, ...):
        # Change from:
        await user_client.get_user(driver_id)
        # To:
        await message_queue.send("get_user", driver_id)

# Routes don't change!
```

---

<a name="part5-3"></a>
## 30. Service Layer in Practice

**Your implementation** (`services/ride_service.py`):

```python
class RideService:
    """Service for ride CRUD operations"""

    async def create_ride(self, ride_data: RideCreate, driver_id: str, db: AsyncSession):
        # Business logic
        driver = await user_client.get_user(driver_id)
        if not driver:
            raise ValueError("Driver not found")

        ride = Ride(
            driver_id=driver_id,
            origin_address=ride_data.origin.address,
            # ... all fields
        )

        db.add(ride)
        await db.commit()
        await db.refresh(ride)
        return ride

    async def get_ride(self, ride_id: str, db: AsyncSession):
        query = select(Ride).where(Ride.id == ride_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search_rides(self, params: RideSearchParams, db: AsyncSession):
        # Complex search logic
        query = select(Ride).where(...)
        result = await db.execute(query)
        rides = result.scalars().all()

        # Filter by distance
        filtered = []
        for ride in rides:
            if haversine_distance(...) <= params.proximity_km:
                filtered.append(ride)

        return filtered

# Single instance
ride_service = RideService()
```

### Singleton Pattern

```python
# At module level
ride_service = RideService()
```

**This creates ONE instance shared by all requests.**

**Why?**
- No state (service is stateless)
- Database session passed as parameter (not stored)
- No need for multiple instances

**Usage everywhere:**
```python
from app.services.ride_service import ride_service

await ride_service.create_ride(...)
await ride_service.get_ride(...)
```

---

# PART 6: USER REGISTRATION FLOW

<a name="part6-1"></a>
## 31. Complete Registration Implementation

**From `routes/users.py:14`:**

```python
@router.post("/", response_model=UserResponse)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
):
    """Create new user."""

    # 1. Check if user already exists
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(400, "The user with this user name already exists in the system.")

    # 2. Create new user object
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
    )

    # 3. Save to DB
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user
```

### Step-by-Step Breakdown

**Step 1: Check duplicate email**
```python
query = select(User).where(User.email == user_in.email)
result = await db.execute(query)
existing_user = result.scalar_one_or_none()
```

**Why?**
- Email is unique (`Column(String, unique=True)`)
- Database would reject duplicate
- But database error is ugly: "duplicate key value violates unique constraint"
- Better to check first and return nice error

**Step 2: Hash password**
```python
hashed_password=security.get_password_hash(user_in.password)
```

**Input:** `"MyPassword123!"`
**Output:** `"$2b$12$abcdef..."` (bcrypt hash)

**NEVER store plain password!**

**Step 3: Create user object**
```python
user = User(
    email=user_in.email,
    hashed_password=...,
    full_name=user_in.full_name,
    phone_number=user_in.phone_number,
)
```

**This creates Python object, NOT in database yet!**

**Step 4: Add to session**
```python
db.add(user)
```

**Still not in database! Just queued.**

**Step 5: Commit**
```python
await db.commit()
```

**NOW it's in database!**

Generated SQL:
```sql
INSERT INTO users (email, hashed_password, full_name, phone_number, is_active, created_at)
VALUES ('john@sjsu.edu', '$2b$12...', 'John Doe', '4081234567', true, NOW())
RETURNING id;
```

**Step 6: Refresh**
```python
await db.refresh(user)
```

**Why refresh?**
- Database generated fields: `id`, `created_at`, `updated_at`
- `refresh()` fetches them from database
- Now `user.id` and `user.created_at` are populated

**Step 7: Return**
```python
return user
```

**FastAPI automatically:**
- Converts `User` object to `UserResponse` schema
- Excludes `hashed_password` (not in schema)
- Converts to JSON

---

<a name="part6-2"></a>
## 32. Duplicate Email Handling

### Database Constraint

```python
email = Column(String, unique=True, index=True, nullable=False)
```

**Generated SQL:**
```sql
CREATE TABLE users (
    email VARCHAR UNIQUE NOT NULL
);

CREATE UNIQUE INDEX ix_users_email ON users(email);
```

### Without Explicit Check

```python
# No duplicate check
user = User(email="john@sjsu.edu", ...)
db.add(user)
await db.commit()  # Might raise IntegrityError!
```

**Error:**
```
sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint "users_email_key"
Detail: Key (email)=(john@sjsu.edu) already exists.
```

**User sees:**
```json
{
  "detail": "Internal Server Error"
}
```

**Not helpful!**

### With Explicit Check

```python
existing = await db.execute(select(User).where(User.email == user_in.email))
if existing.scalar_one_or_none():
    raise HTTPException(400, "The user with this user name already exists in the system.")
```

**User sees:**
```json
{
  "detail": "The user with this user name already exists in the system."
}
```

**Much better!**

### Exception Handling Alternative

```python
try:
    user = User(email=user_in.email, ...)
    db.add(user)
    await db.commit()
except IntegrityError:
    raise HTTPException(400, "Email already exists")
```

**Works, but:**
- Less efficient (tries to insert, then rolls back)
- Less clear (exception for control flow)

**Prefer explicit check!**

---

<a name="part6-3"></a>
## 33. Database Refresh Pattern

### Why Refresh?

**After creating object:**
```python
user = User(email="john@sjsu.edu")
db.add(user)
await db.commit()

print(user.id)  # None? 😱
print(user.created_at)  # None? 😱
```

**Problem:** Database-generated fields aren't in Python object yet.

**Database has:**
```sql
INSERT INTO users (...) VALUES (...) RETURNING id;
-- Returns: id=123, created_at=2024-12-20 10:00:00
```

**But Python object doesn't know!**

### Solution: Refresh

```python
await db.refresh(user)
print(user.id)  # 123 ✓
print(user.created_at)  # 2024-12-20 10:00:00 ✓
```

**What refresh does:**
```sql
SELECT id, email, created_at, updated_at, ...
FROM users
WHERE id = 123;
```

**Fetches all fields from database and updates Python object.**

### When to Refresh

**Always refresh after:**
- Creating new record (to get `id`, `created_at`)
- Updating record (to get `updated_at`)
- Database triggers modify data

**Don't refresh if:**
- You don't need generated fields
- Performance critical (extra query)

### Alternative: RETURNING Clause

SQLAlchemy can fetch generated fields automatically:

```python
from sqlalchemy import insert

stmt = insert(User).values(email="john@sjsu.edu").returning(User)
result = await db.execute(stmt)
user = result.scalar_one()

# user.id is already populated!
```

**But using ORM (db.add) is simpler for most cases.**

---

# PART 7: DOCKER COMPOSE ADVANCED

<a name="part7-1"></a>
## 34. Service Dependencies

**From `docker-compose.yml:18`:**

```yaml
user-service:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy

ride-service:
  depends_on:
    postgres:
      condition: service_healthy
    user-service:
      condition: service_started
```

### What depends_on Does

**Without depends_on:**
```bash
docker-compose up
# Starts all services simultaneously
# ride-service starts before postgres is ready
# Error: "Can't connect to database"
```

**With depends_on:**
```bash
docker-compose up
# 1. Starts postgres
# 2. Waits for postgres health check
# 3. Starts redis
# 4. Waits for redis health check
# 5. Starts user-service
# 6. Starts ride-service (waits for user-service to start, not be healthy)
```

### Condition Types

**service_healthy:**
```yaml
postgres:
  condition: service_healthy
```

Waits for health check to pass:
```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
```

**service_started:**
```yaml
user-service:
  condition: service_started
```

Just waits for container to start (doesn't check if app is ready).

**Why different?**
- Postgres: Has health check → use `service_healthy`
- User-service: Might not have health check → use `service_started`

### Startup Order

```
postgres (starts)
  ↓ (health check passes)
redis (starts)
  ↓ (health check passes)
user-service (starts)
  ↓ (container starts)
ride-service (starts)
```

### Circular Dependencies

**Bad:**
```yaml
user-service:
  depends_on:
    - ride-service

ride-service:
  depends_on:
    - user-service
```

**Error:** Circular dependency!

**Solution:** One-way dependency (ride-service → user-service)

---

<a name="part7-2"></a>
## 35. Container Communication

### Network

**From `docker-compose.yml:105`:**

```yaml
networks:
  rideshare-network:
    driver: bridge

services:
  user-service:
    networks:
      - rideshare-network

  ride-service:
    networks:
      - rideshare-network
```

### How Services Talk

**Ride service calls user service:**

```python
# In ride-service
USER_SERVICE_URL = "http://user-service:8000"
#                          ^^^^^^^^^^^^ hostname

response = await httpx.get(f"{USER_SERVICE_URL}/api/v1/users/123")
```

**How it works:**

1. `user-service` hostname resolves to user-service container IP
2. Docker DNS: `user-service` → `172.18.0.2` (example)
3. Request sent to `http://172.18.0.2:8000/api/v1/users/123`

### Port Mapping

**From `docker-compose.yml`:**

```yaml
user-service:
  ports:
    - "8001:8000"
#      ^^^^  ^^^^
#      host  container

ride-service:
  ports:
    - "8002:8000"
```

**Two ways to access:**

**From your machine:**
```bash
curl http://localhost:8001/health  # user-service
curl http://localhost:8002/health  # ride-service
```

**From ride-service container:**
```bash
curl http://user-service:8000/health  # Use container port!
```

**Why different ports?**
- Host (your machine): 8001, 8002 (to avoid conflicts)
- Container: Both use 8000 (isolated networks, no conflict)

---

<a name="part7-3"></a>
## 36. Volume Mounting for Development

**From `docker-compose.yml:17`:**

```yaml
user-service:
  volumes:
    - ./services/user-service:/app
#     ^^^^^^^^^^^^^^^^^^^^^^^^  ^^^^
#     Host path                 Container path
```

### What This Does

**Your machine:**
```
/Users/you/RideShare/backend/services/user-service/
├── app/
│   ├── main.py
│   └── ...
```

**Container:**
```
/app/
├── app/
│   ├── main.py  ← Same file!
│   └── ...
```

**It's the SAME file!**

### Hot Reload in Action

**1. Edit file on your machine:**
```python
# Edit /Users/you/.../main.py
app = FastAPI(title="New Title")
```

**2. File instantly appears in container:**
```python
# /app/app/main.py in container
app = FastAPI(title="New Title")
```

**3. Uvicorn detects change:**
```
INFO:     Detected file change in 'app/main.py'. Reloading...
```

**4. Server restarts automatically**

**5. Test immediately:**
```bash
curl http://localhost:8001/docs
# See "New Title"
```

**No need to rebuild container!**

### Without Volume

```yaml
# No volumes
user-service:
  build: ./services/user-service
```

**Workflow:**
1. Edit code
2. Stop container: `docker-compose down`
3. Rebuild: `docker-compose build`
4. Start: `docker-compose up`
5. Wait 30 seconds...
6. Test

**With volume:** Edit → Test (2 seconds!)

---

# PART 8: REAL-WORLD SCENARIOS

<a name="part8-1"></a>
## 37. Handling Concurrent Requests

### The Problem

**Two users register with same email simultaneously:**

```
Time 0: User A sends POST /users {"email": "john@sjsu.edu"}
Time 0: User B sends POST /users {"email": "john@sjsu.edu"}

Time 1: Request A checks if email exists → No
Time 1: Request B checks if email exists → No

Time 2: Request A creates user
Time 2: Request B creates user

Result: ERROR or duplicate users?
```

### Solution 1: Database Constraint (What You Have)

```python
email = Column(String, unique=True)
```

**What happens:**
```
Request A: INSERT INTO users (email) VALUES ('john@sjsu.edu')  → SUCCESS
Request B: INSERT INTO users (email) VALUES ('john@sjsu.edu')  → ERROR
```

Database rejects the second insert!

**Your code:**
```python
existing = await db.execute(select(User).where(User.email == user_in.email))
if existing.scalar_one_or_none():
    raise HTTPException(400, "Email exists")

# Still possible for race condition between check and insert!
# But database constraint prevents actual duplicate
```

### Solution 2: Database Lock

```python
async def create_user(user_in, db):
    # Lock the email (prevents concurrent checks)
    await db.execute(
        text("SELECT email FROM users WHERE email = :email FOR UPDATE"),
        {"email": user_in.email}
    )

    # Now safe to check and insert
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email exists")

    user = User(email=user_in.email, ...)
    db.add(user)
    await db.commit()
```

**FOR UPDATE** locks the row until transaction commits.

### Solution 3: Try/Except

```python
try:
    user = User(email=user_in.email, ...)
    db.add(user)
    await db.commit()
except IntegrityError:
    raise HTTPException(400, "Email already exists")
```

**Simplest and works well!**

---

<a name="part8-2"></a>
## 38. Error Handling Across Services

### The Problem

**Ride service calls user service:**

```python
driver = await user_client.get_user(driver_id)
# What if user service is down?
# What if it returns 500 error?
# What if network times out?
```

### Your Implementation

**From `clients/user_client.py:18`:**

```python
async def get_user(self, user_id: str):
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Error fetching user {user_id}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error connecting to user service: {e}")
        return None
```

**Handles:**
- 200: Success → Return data
- 404: User not found → Return None
- Other errors: Log and return None
- Network errors: Log and return None

**Caller handles None:**
```python
driver = await user_client.get_user(driver_id)
if not driver:
    raise ValueError("Driver not found")
```

### Retry Logic (Advanced)

```python
async def get_user_with_retry(self, user_id: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.get_user(user_id)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Retries:**
- Attempt 1: Fails → Wait 1 second
- Attempt 2: Fails → Wait 2 seconds
- Attempt 3: Fails → Raise error

### Circuit Breaker (Advanced)

```python
class UserServiceClient:
    def __init__(self):
        self.failures = 0
        self.circuit_open = False

    async def get_user(self, user_id):
        if self.circuit_open:
            raise Exception("Circuit breaker open, user service unavailable")

        try:
            # Call service
            self.failures = 0  # Reset on success
        except Exception:
            self.failures += 1
            if self.failures >= 5:
                self.circuit_open = True  # Stop trying after 5 failures
            raise
```

**Prevents cascading failures!**

---

<a name="part8-3"></a>
## 39. Logging in Distributed Systems

### The Problem

**Request flow:**
```
User → ride-service → user-service → database
```

**Logs:**

ride-service:
```
2024-12-20 10:00:00 - Creating ride
```

user-service:
```
2024-12-20 10:00:01 - Fetching user 123
```

**Which ride creation triggered which user fetch?** 🤔

### Solution 1: Request ID

**ride-service:**
```python
import uuid

request_id = str(uuid.uuid4())
logger.info(f"[{request_id}] Creating ride")

# Pass to user service
headers = {"X-Request-ID": request_id}
await user_client.get_user(driver_id, headers=headers)
```

**user-service:**
```python
request_id = request.headers.get("X-Request-ID")
logger.info(f"[{request_id}] Fetching user {user_id}")
```

**Logs:**
```
ride-service: [abc-123] Creating ride
user-service: [abc-123] Fetching user 123
```

**Now you can trace the entire request!**

### Solution 2: Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "Creating ride",
    request_id=request_id,
    user_id=user_id,
    service="ride-service"
)
```

**Output (JSON):**
```json
{
  "event": "Creating ride",
  "request_id": "abc-123",
  "user_id": 123,
  "service": "ride-service",
  "timestamp": "2024-12-20T10:00:00Z"
}
```

**Benefits:**
- Easy to search (all logs with `request_id=abc-123`)
- Can send to log aggregation (Elasticsearch, Datadog)
- Machine-readable

---

# Congratulations!

You've completed the advanced topics guide! You now understand:

✅ **Alembic migrations** - Managing database schema changes
✅ **Microservices** - Building and connecting multiple services
✅ **Service-to-service communication** - HTTP clients with HTTPX
✅ **Geospatial features** - Haversine formula and proximity search
✅ **Advanced Pydantic** - Nested schemas, validators, query parameters
✅ **Service layer pattern** - Separating business logic
✅ **Advanced Docker Compose** - Dependencies, networking, volumes
✅ **Real-world scenarios** - Concurrency, error handling, distributed logging

Keep this guide as reference as you continue building your RideShare application!

**Next up:** Section 4 (Google Maps integration), Section 5 (Smart matching algorithm), and beyond!

Happy coding! 🚀
