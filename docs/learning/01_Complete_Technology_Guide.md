# RideShare Academy: Complete Technology Guide
## Your Journey from Zero to Full-Stack Developer

**Welcome!** This document will teach you every single technology we're using in this project, from the ground up. By the end, you'll understand not just *how* things work, but *why* we built them this way.

---

# Table of Contents

## Part 1: The Foundation
1. [What is a Web Application?](#part1-1)
2. [HTTP Protocol - The Language of the Web](#part1-2)
3. [APIs and REST](#part1-3)
4. [JSON - The Data Format](#part1-4)

## Part 2: Python & FastAPI
5. [Why Python for Backend?](#part2-1)
6. [What is FastAPI?](#part2-2)
7. [Async/Await - The Secret to Performance](#part2-3)
8. [Decorators Explained](#part2-4)
9. [Type Hints and Pydantic](#part2-5)
10. [Dependency Injection](#part2-6)
11. [Middleware - The Request Pipeline](#part2-7)

## Part 3: Databases
12. [What is PostgreSQL?](#part3-1)
13. [SQL vs ORM](#part3-2)
14. [SQLAlchemy - The Python Database Layer](#part3-3)
15. [Database Models and Tables](#part3-4)
16. [Relationships and Foreign Keys](#part3-5)
17. [Database Sessions and Transactions](#part3-6)

## Part 4: Redis
18. [What is Redis?](#part4-1)
19. [Key-Value Stores vs Relational Databases](#part4-2)
20. [When to Use Redis](#part4-3)

## Part 5: Authentication & Security
21. [Password Security - Why Never Store Plain Passwords](#part5-1)
22. [Hashing with Bcrypt](#part5-2)
23. [What is JWT (JSON Web Tokens)?](#part5-3)
24. [OAuth2 Flow](#part5-4)
25. [Protected Routes](#part5-5)
26. [CORS - Cross-Origin Resource Sharing](#part5-6)

## Part 6: Docker & Containerization
27. [What is Docker?](#part6-1)
28. [Containers vs Virtual Machines](#part6-2)
29. [Dockerfile Explained](#part6-3)
30. [Docker Compose - Orchestration](#part6-4)
31. [Volumes - Persistent Data](#part6-5)
32. [Networks - Container Communication](#part6-6)
33. [Health Checks](#part6-7)

## Part 7: Architecture
34. [Monolithic vs Microservices](#part7-1)
35. [Why Microservices for RideShare?](#part7-2)
36. [Service Communication Patterns](#part7-3)
37. [Project Structure Best Practices](#part7-4)

## Part 8: Development Workflow
38. [Environment Variables](#part8-1)
39. [Logging Best Practices](#part8-2)
40. [Error Handling](#part8-3)
41. [Hot Reloading](#part8-4)
42. [Testing Basics](#part8-5)

## Part 9: File-by-File Code Walkthrough
43. [Understanding main.py](#part9-1)
44. [Understanding config.py](#part9-2)
45. [Understanding models/user.py](#part9-3)
46. [Understanding schemas/user.py](#part9-4)
47. [Understanding security.py](#part9-5)
48. [Understanding deps.py](#part9-6)
49. [Understanding routes/auth.py](#part9-7)

## Part 10: Common Questions & Troubleshooting
50. [FAQ](#part10-1)
51. [Common Errors and Solutions](#part10-2)
52. [Next Steps](#part10-3)

---

# PART 1: THE FOUNDATION

<a name="part1-1"></a>
## 1. What is a Web Application?

### The Restaurant Analogy
Think of a web application like a restaurant:

- **Frontend (React Native App)**: The dining area where customers sit and place orders
- **Backend (FastAPI)**: The kitchen where food is prepared
- **Database (PostgreSQL)**: The pantry where ingredients are stored
- **API**: The waiter who takes orders from customers to the kitchen and brings food back

### How They Work Together

```
[Your Phone App]
    ↓ (HTTP Request: "Show me available rides")
[Backend API]
    ↓ (Query: "SELECT * FROM rides WHERE...")
[Database]
    ↑ (Returns: List of rides)
[Backend API]
    ↑ (HTTP Response: JSON with ride data)
[Your Phone App displays the rides]
```

### The Request-Response Cycle

Every web interaction follows this pattern:

1. **Client** (browser/app) sends a **Request** ("I want data")
2. **Server** (our FastAPI) receives it
3. **Server** processes it (maybe checks database)
4. **Server** sends back a **Response** ("Here's your data")
5. **Client** displays the result

**Example from our app:**
```python
# When a user hits the health endpoint
# Request: GET http://localhost:8001/health
# Response: {"status": "healthy", "checks": {...}}
```

---

<a name="part1-2"></a>
## 2. HTTP Protocol - The Language of the Web

### What is HTTP?

HTTP (HyperText Transfer Protocol) is like a language that computers use to talk to each other over the internet.

### HTTP Methods (Verbs)

Think of these as actions you can perform:

| Method | Purpose | Example | In Our App |
|--------|---------|---------|------------|
| **GET** | Retrieve data | "Show me the menu" | Get user profile |
| **POST** | Create new data | "Place an order" | Register new user |
| **PUT** | Update existing data | "Change my order" | Update profile |
| **DELETE** | Remove data | "Cancel my order" | Delete account |

### HTTP Status Codes

These are like receipts that tell you what happened:

| Code | Meaning | Example |
|------|---------|---------|
| **200** | Success | "Your order is ready" |
| **201** | Created | "New account created" |
| **400** | Bad Request | "You can't order pizza here, we're a burger joint" |
| **401** | Unauthorized | "You need to login first" |
| **403** | Forbidden | "You don't have permission" |
| **404** | Not Found | "That page doesn't exist" |
| **500** | Server Error | "Our kitchen is on fire" |

### Headers

Headers are like metadata - extra information about the request/response.

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
X-Process-Time: 45.23ms
```

**Real example from our code:**
```python
# In logging_middleware.py:34
response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
```

---

<a name="part1-3"></a>
## 3. APIs and REST

### What is an API?

**API** = Application Programming Interface

It's a contract that says: "If you ask me in this specific way, I'll give you what you want."

**Example:**
- You ask: `GET /api/v1/users/123`
- API responds: `{"id": 123, "name": "John", "email": "john@sjsu.edu"}`

### What is REST?

**REST** = Representational State Transfer

It's a style of building APIs with these principles:

1. **Stateless**: Each request is independent (server doesn't remember you between requests)
2. **Resource-based**: Everything is a "resource" with a URL (`/users`, `/rides`)
3. **Uses HTTP methods**: GET, POST, PUT, DELETE
4. **Returns data in standard format**: Usually JSON

### RESTful Route Design

Good REST API design:

```
GET    /api/v1/users          → List all users
POST   /api/v1/users          → Create new user
GET    /api/v1/users/123      → Get user 123
PUT    /api/v1/users/123      → Update user 123
DELETE /api/v1/users/123      → Delete user 123
```

**In our code** (from `main.py:46`):
```python
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
```

This creates routes like:
- `POST /api/v1/auth/login/access-token`
- `GET /api/v1/users/me`

---

<a name="part1-4"></a>
## 4. JSON - The Data Format

### What is JSON?

**JSON** = JavaScript Object Notation

It's a text format for storing and transporting data. Think of it as a universal language that all programming languages understand.

### JSON Syntax

```json
{
  "name": "John Doe",
  "age": 21,
  "email": "john@sjsu.edu",
  "is_verified": true,
  "courses": ["CMPE 172", "CMPE 202"],
  "address": {
    "street": "1 Washington Square",
    "city": "San Jose"
  }
}
```

### JSON Types

- **String**: `"hello"` (must use double quotes)
- **Number**: `42`, `3.14`
- **Boolean**: `true`, `false`
- **Null**: `null`
- **Array**: `[1, 2, 3]`
- **Object**: `{"key": "value"}`

### Python ↔ JSON Conversion

Python dictionaries automatically convert to JSON in FastAPI:

```python
# In health.py:17
health_status = {
    "status": "healthy",
    "service": settings.SERVICE_NAME,
    "timestamp": datetime.utcnow().isoformat(),
    "checks": {}
}
return health_status
```

FastAPI automatically converts this Python dict to JSON:
```json
{
  "status": "healthy",
  "service": "user-service",
  "timestamp": "2024-12-20T10:00:00.000Z",
  "checks": {}
}
```

---

# PART 2: PYTHON & FASTAPI

<a name="part2-1"></a>
## 5. Why Python for Backend?

### Advantages

1. **Readable**: Code looks like English
2. **Fast Development**: Less code to write
3. **Huge Ecosystem**: Libraries for everything
4. **Great for APIs**: FastAPI, Django, Flask
5. **Data Science Integration**: Easy to add ML features later

### Python vs Other Languages

| Language | Speed | Dev Speed | Use Case |
|----------|-------|-----------|----------|
| Python | Medium | Fast | APIs, ML, Scripts |
| JavaScript/Node | Medium | Fast | APIs, Real-time |
| Go | Very Fast | Medium | High-performance services |
| Java | Fast | Slow | Enterprise systems |

**For our project**: Python is perfect because we want rapid development and might add ML features (ride matching algorithm) later.

---

<a name="part2-2"></a>
## 6. What is FastAPI?

### The Simple Explanation

FastAPI is a web framework. It handles all the boring stuff so you can focus on your business logic.

**What FastAPI does for you:**
1. Routes requests to the right function
2. Validates incoming data
3. Converts data to/from JSON
4. Generates API documentation automatically
5. Handles errors gracefully

### FastAPI vs Others

| Framework | Speed | Learning Curve | Documentation |
|-----------|-------|----------------|---------------|
| **FastAPI** | ⚡⚡⚡ | Easy | Auto-generated |
| Flask | ⚡⚡ | Very Easy | Manual |
| Django | ⚡ | Hard | Excellent |

### Why FastAPI for RideShare?

1. **Performance**: As fast as Node.js/Go
2. **Type Safety**: Catches bugs before runtime
3. **Auto Docs**: Swagger UI for free
4. **Async Support**: Handles thousands of users
5. **Modern**: Uses latest Python features

### Your First FastAPI Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

Run it:
```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000 → See `{"message": "Hello World"}`
Visit: http://localhost:8000/docs → See interactive API docs

---

<a name="part2-3"></a>
## 7. Async/Await - The Secret to Performance

### The Problem: Blocking I/O

**Traditional (Synchronous) Code:**

```python
def get_user():
    user = database.query()  # Waits 100ms
    return user

def get_rides():
    rides = database.query()  # Waits 100ms
    return rides

# This takes 200ms total (100 + 100)
user = get_user()
rides = get_rides()
```

**The Waiter Analogy:**

Imagine a restaurant with ONE waiter (your server):

**Synchronous (Normal Python):**
1. Waiter takes order from Customer 1
2. Waiter walks to kitchen
3. Waiter **STANDS THERE** watching chef cook (10 minutes)
4. Waiter brings food
5. NOW waiter can serve Customer 2

**Problem:** If 10 customers arrive, Customer 10 waits 100 minutes!

**Asynchronous (Async Python):**
1. Waiter takes order from Customer 1
2. Waiter gives order to kitchen
3. While food cooks, waiter serves Customer 2, 3, 4...
4. When food is ready, waiter delivers it

**Benefit:** All 10 customers get served simultaneously!

### The Solution: Async/Await

```python
async def get_user():
    user = await database.query()  # Doesn't block, can serve others
    return user

async def get_rides():
    rides = await database.query()  # Doesn't block
    return rides

# This STILL takes 200ms, but server can handle other requests meanwhile
user = await get_user()
rides = await get_rides()
```

### Real Example from Our Code

**In `health.py:29`:**
```python
async def health_check():
    # Check Database Connection
    try:
        conn = await asyncpg.connect(db_url)  # 'await' lets other requests run
        await conn.close()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["checks"]["database"] = f"disconnected: {str(e)}"
```

### Key Rules

1. `async def` = This function can pause without blocking
2. `await` = Pause here, let others run, resume when ready
3. You can only `await` inside `async def`
4. Database/Network calls should always be `await`

### Performance Impact

**Without Async:**
- 1 request = 100ms
- 10 requests = 1000ms (serial)
- Server handles: ~10 requests/second

**With Async:**
- 1 request = 100ms
- 10 requests = 100ms (parallel)
- Server handles: ~1000 requests/second

**100x improvement!**

---

<a name="part2-4"></a>
## 8. Decorators Explained

### What is a Decorator?

A decorator is a function that wraps another function to modify its behavior.

**The Coffee Analogy:**
- You have a function: `make_coffee()`
- You want to add milk: `@add_milk`
- You want to add sugar: `@add_sugar`

```python
@add_sugar
@add_milk
def make_coffee():
    return "Coffee"

# Result: "Coffee with milk and sugar"
```

### How Decorators Work

```python
# Without decorator
def greet():
    return "Hello"

# With decorator
@make_uppercase
def greet():
    return "Hello"

# Returns: "HELLO"
```

**What happened?**
```python
# This:
@make_uppercase
def greet():
    return "Hello"

# Is equivalent to:
def greet():
    return "Hello"
greet = make_uppercase(greet)
```

### FastAPI Decorators

**In our code (`health.py:9`):**
```python
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    ...
```

**What this does:**
1. `@router.get("/health")` tells FastAPI: "When someone visits `/health` with GET method, run this function"
2. `status_code=200` tells FastAPI: "Return 200 OK by default"

**Without the decorator**, `health_check()` is just a normal function that never runs.

### Multiple Decorators

```python
@app.get("/users")
@require_authentication
@log_request
async def get_users():
    return users
```

Order matters! They execute from bottom to top:
1. `log_request` runs first
2. `require_authentication` runs second
3. Finally your function runs

---

<a name="part2-5"></a>
## 9. Type Hints and Pydantic

### Why Type Hints?

**Without type hints:**
```python
def add(a, b):
    return a + b

add(5, 3)       # 8
add("5", "3")   # "53"  😱 Bug!
```

**With type hints:**
```python
def add(a: int, b: int) -> int:
    return a + b

add(5, 3)       # 8 ✓
add("5", "3")   # IDE warns you BEFORE running!
```

### Type Hints in Python

```python
# Variables
name: str = "John"
age: int = 21
is_student: bool = True
height: float = 5.9

# Functions
def greet(name: str) -> str:
    return f"Hello {name}"

# Lists
names: list[str] = ["Alice", "Bob"]
numbers: list[int] = [1, 2, 3]

# Dictionaries
user: dict[str, any] = {"name": "John", "age": 21}

# Optional (can be None)
from typing import Optional
phone: Optional[str] = None
```

### Pydantic - Type Hints on Steroids

Pydantic validates data automatically.

**Example from `config.py:4`:**
```python
class Settings(BaseSettings):
    SERVICE_NAME: str = "user-service"
    DEBUG: bool = False
    DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

**What Pydantic does:**

If you set `DEBUG=yes` in your `.env` file:
- Pydantic sees `DEBUG: bool`
- Automatically converts `"yes"` → `True`

If you set `ACCESS_TOKEN_EXPIRE_MINUTES=hello`:
- Pydantic sees `int`
- **Crashes at startup**: "Cannot convert 'hello' to int"
- **You find the bug before users do!**

### User Schemas

**From `schemas/user.py:19`:**
```python
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
```

**What this does:**
```python
# Valid
user = UserBase(email="john@sjsu.edu", full_name="John")  ✓

# Invalid - Pydantic rejects it
user = UserBase(email="not-an-email", full_name="John")  ✗
# Error: "value is not a valid email address"
```

### Validation in Action

**From `schemas/user.py:26`:**
```python
class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
```

Now FastAPI automatically validates:
```python
# Good password
POST /register {"password": "MyPassword123!"}  ✓

# Bad password
POST /register {"password": "123"}
# Response: {"detail": "Password must be at least 8 characters long"}
```

---

<a name="part2-6"></a>
## 10. Dependency Injection

### The Problem

You need database connection in many routes:

```python
@app.get("/users")
def get_users():
    db = Database()  # Create connection
    db.connect()
    users = db.query("SELECT * FROM users")
    db.close()
    return users

@app.get("/rides")
def get_rides():
    db = Database()  # Duplicate code! 😭
    db.connect()
    rides = db.query("SELECT * FROM rides")
    db.close()
    return rides
```

**Problems:**
1. Duplicate code everywhere
2. Hard to test (how to mock the database?)
3. Easy to forget `db.close()` → memory leak

### The Solution: Dependency Injection

**Define the dependency once** (`session.py:25`):
```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Use it everywhere** (`deps.py:19`):
```python
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    # db is automatically provided by FastAPI!
    query = select(User).where(User.id == int(token_data.sub))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user
```

### How It Works

When you call a route:

```python
@app.get("/users/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

FastAPI does this behind the scenes:
1. Calls `get_db()` → creates database session
2. Passes `db` to `get_current_user(db)`
3. `get_current_user` returns the user
4. Passes `user` to `get_my_profile(user)`
5. Automatically closes database session

**You just write:**
```python
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

**FastAPI handles all the plumbing!**

### Nested Dependencies

Dependencies can depend on other dependencies:

```python
get_my_profile
  ↓ depends on
get_current_user
  ↓ depends on
get_db
```

---

<a name="part2-7"></a>
## 11. Middleware - The Request Pipeline

### What is Middleware?

Middleware is code that runs **before** and **after** every request.

Think of it like airport security:

```
[Passenger arrives]
  ↓
[Security Check 1: ID Check] ← Middleware
  ↓
[Security Check 2: X-ray] ← Middleware
  ↓
[Board Plane] ← Your Route Handler
  ↓
[Security logs: "Passenger boarded"] ← Middleware
  ↓
[Passenger leaves]
```

### Request Flow with Middleware

```
Client sends request
  ↓
[Logging Middleware]: Starts timer
  ↓
[CORS Middleware]: Checks origin
  ↓
[Your Route Handler]: Processes request
  ↓
[Logging Middleware]: Logs duration
  ↓
Response sent to client
```

### Example: Logging Middleware

**From `logging_middleware.py:7`:**
```python
async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request (run the actual route handler)
    response = await call_next(request)

    # Calculate processing time
    process_time = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.2f}ms"
    )

    # Add processing time to headers
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

    return response
```

**What this does:**

When you visit `/health`:

```
[Middleware starts]
2024-12-20 10:00:00 - INFO - Request: GET /health
[Timer starts]

[Your health_check() function runs]

[Timer stops: 45ms elapsed]
2024-12-20 10:00:00 - INFO - Response: GET /health Status: 200 Duration: 45.00ms
[Middleware adds header: X-Process-Time: 45.00ms]
```

### CORS Middleware

**From `main.py:27`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**What is CORS?**

By default, browsers block websites from calling APIs on different domains:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`

Different origins! Browser blocks it by default for security.

CORS middleware adds headers that tell the browser: "It's okay, I allow localhost:3000 to talk to me."

**Headers added:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
```

---

# PART 3: DATABASES

<a name="part3-1"></a>
## 12. What is PostgreSQL?

### The Filing Cabinet Analogy

A database is like a filing cabinet:

- **Database** = The entire cabinet
- **Tables** = Drawers in the cabinet
- **Rows** = Individual folders
- **Columns** = Fields on the folder label (Name, Date, Category)

### PostgreSQL vs Others

| Database | Type | Best For | Our Use |
|----------|------|----------|---------|
| **PostgreSQL** | Relational | Complex queries, transactions | User data, rides, bookings |
| MySQL | Relational | Simple web apps | ❌ |
| MongoDB | NoSQL | Flexible schema | ❌ |
| **Redis** | Key-Value | Caching, real-time data | Session storage, tracking |

### Why PostgreSQL for RideShare?

1. **ACID Transactions**: If payment fails, booking is cancelled automatically
2. **Relationships**: Easy to join users + rides + bookings
3. **Advanced Features**: Geospatial queries for "rides near me"
4. **Free & Open Source**
5. **Industry Standard**: Used by Instagram, Spotify, Reddit

### Basic SQL Concepts

**Tables:**
```sql
users table:
+----+-------------------+--------------+
| id | email             | full_name    |
+----+-------------------+--------------+
| 1  | john@sjsu.edu     | John Doe     |
| 2  | alice@sjsu.edu    | Alice Smith  |
+----+-------------------+--------------+

rides table:
+----+-----------+------------------+-------+
| id | driver_id | destination      | seats |
+----+-----------+------------------+-------+
| 1  | 1         | San Francisco    | 3     |
| 2  | 2         | Santa Cruz       | 4     |
+----+-----------+------------------+-------+
```

**Queries:**
```sql
-- Get all users
SELECT * FROM users;

-- Get one user
SELECT * FROM users WHERE id = 1;

-- Create user
INSERT INTO users (email, full_name) VALUES ('bob@sjsu.edu', 'Bob');

-- Update user
UPDATE users SET full_name = 'Robert' WHERE id = 3;

-- Delete user
DELETE FROM users WHERE id = 3;

-- Join tables
SELECT users.full_name, rides.destination
FROM rides
JOIN users ON rides.driver_id = users.id;
```

---

<a name="part3-2"></a>
## 13. SQL vs ORM

### The Translation Analogy

**SQL** = Speaking Portuguese directly
**ORM** = Using a translator (you speak English, they speak Portuguese for you)

### Writing Raw SQL

```python
# Raw SQL (tedious)
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
user = cursor.fetchone()
print(user[0], user[1], user[2])  # What is column 2?
```

**Problems:**
1. Write SQL strings (easy to make mistakes)
2. Remember column positions
3. Convert rows to Python objects manually
4. SQL injection vulnerabilities

### Using ORM (SQLAlchemy)

```python
# ORM (clean)
user = db.query(User).filter(User.email == email).first()
print(user.id, user.email, user.full_name)  # Clear!
```

**Benefits:**
1. Write Python code
2. Type safety
3. Auto-conversion to Python objects
4. Protection from SQL injection

### SQLAlchemy Example

**Defining a model** (`models/user.py:5`):
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
```

SQLAlchemy automatically creates this SQL:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL
);
```

**Querying:**

```python
# Python ORM
user = await db.execute(select(User).where(User.email == "john@sjsu.edu"))
user = user.scalar_one_or_none()

# Equivalent SQL
SELECT * FROM users WHERE email = 'john@sjsu.edu';
```

---

<a name="part3-3"></a>
## 14. SQLAlchemy - The Python Database Layer

### What is SQLAlchemy?

SQLAlchemy is the most popular Python ORM (Object-Relational Mapper).

**It has 2 layers:**

1. **Core**: Low-level SQL builder
2. **ORM**: High-level Python objects

We use the ORM layer.

### Key Concepts

#### 1. Engine

The engine manages the connection pool to the database.

**From `session.py:8`:**
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries
    future=True
)
```

Think of the engine as a phone line to the database. It maintains multiple connections (pool) so you don't have to reconnect every time.

#### 2. Session

A session is a workspace for database operations.

```python
# Start session
session = AsyncSessionLocal()

# Do work
user = await session.execute(select(User).where(User.id == 1))

# Commit (save changes)
await session.commit()

# Close
await session.close()
```

**Rules:**
- One session per request
- Always close sessions
- Commit to save changes
- Rollback on errors

#### 3. Base

Base is the parent class for all models.

**From `db/base.py`:**
```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

All your models inherit from Base:
```python
class User(Base):
    ...

class Ride(Base):
    ...
```

Base keeps track of all your models and can create all tables at once.

---

<a name="part3-4"></a>
## 15. Database Models and Tables

### What is a Model?

A model is a Python class that represents a database table.

**From `models/user.py:5`:**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Column Types

| Python Type | Database Type | Example |
|-------------|---------------|---------|
| `Integer` | INTEGER | 42 |
| `String(100)` | VARCHAR(100) | "John Doe" |
| `Text` | TEXT | Long text |
| `Boolean` | BOOLEAN | True/False |
| `DateTime` | TIMESTAMP | 2024-12-20 10:00:00 |
| `Numeric(10,2)` | DECIMAL | 99.99 |

### Column Constraints

```python
# Primary Key (unique identifier)
id = Column(Integer, primary_key=True)

# Unique (no duplicates)
email = Column(String, unique=True)

# Not Null (required)
email = Column(String, nullable=False)

# Index (faster lookups)
email = Column(String, index=True)

# Default Value
is_active = Column(Boolean, default=True)

# Server Default (database generates value)
created_at = Column(DateTime, server_default=func.now())
```

### Timestamps

**Always add these** (`models/user.py:24`):
```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Why?**
- `created_at`: When was this record created?
- `updated_at`: When was it last modified?
- Crucial for debugging and auditing

---

<a name="part3-5"></a>
## 16. Relationships and Foreign Keys

### What is a Foreign Key?

A foreign key creates a link between two tables.

**Example:**

```python
users table:
+----+-------------------+
| id | email             |
+----+-------------------+
| 1  | john@sjsu.edu     |
| 2  | alice@sjsu.edu    |
+----+-------------------+

rides table:
+----+-----------+------------------+
| id | driver_id | destination      |  ← driver_id is a foreign key
+----+-----------+------------------+
| 1  | 1         | San Francisco    |  ← driver is user #1 (John)
| 2  | 2         | Santa Cruz       |  ← driver is user #2 (Alice)
+----+-----------+------------------+
```

### Defining Relationships

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)

    # Relationship: One user can have many rides
    rides = relationship("Ride", back_populates="driver")

class Ride(Base):
    __tablename__ = "rides"
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey("users.id"))  # Links to users.id
    destination = Column(String)

    # Relationship: Each ride has one driver
    driver = relationship("User", back_populates="rides")
```

### Using Relationships

```python
# Get user
user = await db.execute(select(User).where(User.id == 1))
user = user.scalar_one()

# Get all rides by this user
print(user.rides)  # [Ride1, Ride2, Ride3]

# Get a ride
ride = await db.execute(select(Ride).where(Ride.id == 1))
ride = ride.scalar_one()

# Get the driver
print(ride.driver.email)  # "john@sjsu.edu"
```

### Types of Relationships

1. **One-to-Many**: One user → Many rides
2. **Many-to-One**: Many rides → One user
3. **Many-to-Many**: Many students → Many courses (requires junction table)
4. **One-to-One**: One user → One profile

---

<a name="part3-6"></a>
## 17. Database Sessions and Transactions

### What is a Transaction?

A transaction is a group of operations that either **all succeed** or **all fail**.

**Example: Booking a ride**

```python
# Start transaction
1. Deduct seat from ride (seats: 3 → 2)
2. Create booking record
3. Charge payment
4. Send notification

# If payment fails at step 3:
# Rollback (undo steps 1-2)
# Result: Seats back to 3, no booking, no charge
```

**This prevents:**
- Charging user but no booking created
- Booking created but seats not deducted
- Inconsistent database state

### ACID Properties

- **Atomicity**: All or nothing
- **Consistency**: Database stays valid
- **Isolation**: Transactions don't interfere
- **Durability**: Committed data is saved permanently

### Session in Our Code

**From `session.py:25`:**
```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Save all changes
        except Exception:
            await session.rollback()  # Undo all changes
            raise
        finally:
            await session.close()  # Close connection
```

**How it works:**

```python
@app.post("/book-ride")
async def book_ride(db: AsyncSession = Depends(get_db)):
    # 1. Start transaction (automatic)

    ride = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride.seats -= 1  # Not saved yet!

    booking = Booking(user_id=user.id, ride_id=ride.id)
    db.add(booking)  # Not saved yet!

    # 2. If no errors, commit (automatic)
    # Both changes saved together

    # 3. If error happens, rollback (automatic)
    # Nothing is saved
```

**Key points:**
- Changes are in-memory until `commit()`
- `commit()` saves everything at once
- `rollback()` discards all changes
- FastAPI dependency handles this automatically

---

# PART 4: REDIS

<a name="part4-1"></a>
## 18. What is Redis?

### The Simple Explanation

Redis is an in-memory database. Think of it as a **super-fast dictionary** stored in RAM.

### Why Redis?

**Speed comparison:**
- **PostgreSQL** (on disk): ~1-10ms per query
- **Redis** (in RAM): ~0.1ms per query

**100x faster!**

### What Redis Does

1. **Caching**: Store frequently-accessed data
2. **Session Storage**: User login sessions
3. **Real-time Data**: Live locations, chat messages
4. **Queues**: Background jobs

### Redis Data Types

```python
# String
SET user:1000:name "John Doe"
GET user:1000:name  # "John Doe"

# Number
SET user:1000:points 100
INCR user:1000:points  # 101

# Hash (like a dictionary)
HSET user:1000 name "John" email "john@sjsu.edu"
HGET user:1000 name  # "John"

# List
LPUSH recent_rides "ride_123" "ride_456"
LRANGE recent_rides 0 10  # Get 10 most recent

# Set (unique values)
SADD online_users "user_1" "user_2"
SMEMBERS online_users  # ["user_1", "user_2"]

# Sorted Set (leaderboard)
ZADD ratings 4.9 "driver_1" 4.7 "driver_2"
ZRANGE ratings 0 10  # Top 10 drivers

# Expiring Keys (auto-delete)
SETEX session:abc123 3600 "user_data"  # Expires in 1 hour
```

---

<a name="part4-2"></a>
## 19. Key-Value Stores vs Relational Databases

### The Difference

**Relational Database (PostgreSQL):**
```
users table:
+----+----------+---------------+
| id | name     | email         |
+----+----------+---------------+
| 1  | John     | john@sjsu.edu |
+----+----------+---------------+

Structure: Tables → Rows → Columns
```

**Key-Value Store (Redis):**
```
Key: "user:1:name"     Value: "John"
Key: "user:1:email"    Value: "john@sjsu.edu"
Key: "session:abc123"  Value: {"user_id": 1, "expires": "..."}

Structure: Key → Value
```

### When to Use Each

| Feature | PostgreSQL | Redis |
|---------|------------|-------|
| Speed | Slower | **Very Fast** |
| Persistence | **Permanent** | Optional |
| Complex Queries | **Yes (JOIN, WHERE)** | No |
| Relationships | **Yes** | No |
| Memory Usage | Low (disk) | **High (RAM)** |
| Use Case | Primary data | Cache, sessions |

### Our Strategy: Use Both!

```
User registers:
1. Save to PostgreSQL (permanent storage)

User logs in:
2. Create session in Redis (fast access)
   SET session:abc123 user_data EX 3600  # Expires in 1 hour

User makes request:
3. Check Redis for session (0.1ms)
4. If needed, query PostgreSQL for full data (1-10ms)
```

**Result:** Fast performance + permanent storage

---

<a name="part4-3"></a>
## 20. When to Use Redis

### Use Case 1: Caching

**Problem:** Same database query runs 1000 times/second
**Solution:** Cache the result

```python
# Check cache first
cached_rides = await redis.get("popular_rides")
if cached_rides:
    return cached_rides  # 0.1ms ⚡

# Not in cache, query database
rides = await db.execute(select(Ride).where(Ride.popular == True))
rides = rides.scalars().all()

# Save to cache for 5 minutes
await redis.setex("popular_rides", 300, json.dumps(rides))
return rides  # 10ms first time, 0.1ms next 1000 times
```

### Use Case 2: Session Storage

**Problem:** Check if user is logged in on every request
**Solution:** Store session in Redis

```python
# Login
session_id = uuid.uuid4()
await redis.setex(f"session:{session_id}", 3600, user.id)
return {"session_id": session_id}

# Subsequent requests
user_id = await redis.get(f"session:{request.session_id}")
if not user_id:
    raise HTTPException(401, "Not logged in")
```

### Use Case 3: Real-Time Tracking

**Problem:** Store driver locations that update every second
**Solution:** Use Redis instead of hammering PostgreSQL

```python
# Update location every second
await redis.setex(
    f"location:driver:{driver_id}",
    60,  # Expire after 60 seconds (if driver goes offline)
    json.dumps({"lat": 37.3352, "lng": -121.8811})
)

# Get all nearby drivers
# (Use Redis geospatial features)
nearby = await redis.georadius("drivers", lng, lat, 5, "km")
```

### Use Case 4: Rate Limiting

**Problem:** Prevent API abuse
**Solution:** Track requests in Redis

```python
# Allow 100 requests per minute
key = f"rate_limit:{user.id}"
count = await redis.incr(key)
if count == 1:
    await redis.expire(key, 60)  # Reset after 60 seconds
if count > 100:
    raise HTTPException(429, "Too many requests")
```

---

# PART 5: AUTHENTICATION & SECURITY

<a name="part5-1"></a>
## 21. Password Security - Why Never Store Plain Passwords

### The Disaster Scenario

**Bad (Never do this):**
```python
# User registers
password = request.password  # "MyPassword123"
db.add(User(password=password))  # Stored as "MyPassword123"
```

**What happens when database is hacked:**
```
users table:
+----+-------------------+----------------+
| id | email             | password       |
+----+-------------------+----------------+
| 1  | john@sjsu.edu     | MyPassword123  |  😱
| 2  | alice@sjsu.edu    | AlicePass456   |  😱
+----+-------------------+----------------+
```

**Hacker now has:**
- Everyone's emails
- Everyone's passwords
- Can login to your app as anyone
- Most people reuse passwords → can access their Gmail, bank, etc.

**Real examples:**
- Adobe (2013): 153 million passwords leaked
- LinkedIn (2012): 117 million passwords leaked
- Yahoo (2014): 3 **billion** accounts

### The Solution: Hashing

**Good (What we do):**
```python
# User registers
password = request.password  # "MyPassword123"
hashed = hash_password(password)  # "$2b$12$abcdef..."
db.add(User(hashed_password=hashed))
```

**Database:**
```
users table:
+----+-------------------+------------------------------------------------------------+
| id | email             | hashed_password                                            |
+----+-------------------+------------------------------------------------------------+
| 1  | john@sjsu.edu     | $2b$12$abcdef...  (unreadable)                              |
| 2  | alice@sjsu.edu    | $2b$12$ghijkl...  (unreadable)                              |
+----+-------------------+------------------------------------------------------------+
```

**Even if hacker steals database:**
- Can't read passwords (hashed)
- Can't login (hash is one-way)
- Can't reverse engineer (bcrypt is designed to be slow)

---

<a name="part5-2"></a>
## 22. Hashing with Bcrypt

### What is Hashing?

Hashing is a one-way mathematical function:

```
Input: "MyPassword123"
  ↓ (hash function)
Output: "$2b$12$abcdefghijklmnopqrstuvwxyz1234567890"
```

**Properties:**
1. **One-way**: Cannot reverse (output → input)
2. **Deterministic**: Same input → same output
3. **Fast to compute**: Milliseconds
4. **Unique**: Different inputs → different outputs

### Why Bcrypt?

**Comparison:**

| Algorithm | Speed | Security | Status |
|-----------|-------|----------|--------|
| MD5 | Very Fast | **Broken** | ❌ Never use |
| SHA1 | Very Fast | **Weak** | ❌ Deprecated |
| SHA256 | Fast | Okay | ⚠️ Too fast for passwords |
| **Bcrypt** | Slow | **Excellent** | ✅ Industry standard |
| Argon2 | Slow | Excellent | ✅ Also good |

**Why "slow" is good for passwords:**
- User login: 100ms delay is fine
- Hacker brute-force: 100ms per guess = 10 guesses/second = 315 million guesses/year
- With SHA256: 1 billion guesses/second = impossible to defend

**Bcrypt is intentionally slow to prevent brute-force attacks.**

### Using Bcrypt in Our Code

**From `security.py:9`:**
```python
# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Example:**
```python
# Registration
password = "MyPassword123"
hashed = get_password_hash(password)
# Result: "$2b$12$abcdefghijklmnopqrstuvwxyz1234567890"
db.add(User(hashed_password=hashed))

# Login
entered_password = "MyPassword123"
stored_hash = user.hashed_password
if verify_password(entered_password, stored_hash):
    print("Correct password!")  ✓
else:
    print("Wrong password!")
```

### Salt

Bcrypt automatically adds a **salt** (random data):

```
Hash of "password" without salt: same every time
→ Hacker can use rainbow tables (precomputed hashes)

Hash of "password" with salt: different every time
User 1: $2b$12$abc... (salt: abc...)
User 2: $2b$12$xyz... (salt: xyz...)
→ Rainbow tables useless
```

**Bcrypt handles salts automatically. You don't have to think about it.**

---

<a name="part5-3"></a>
## 23. What is JWT (JSON Web Tokens)?

### The Problem: Stateless Authentication

**Old way (Session-based):**
```
User logs in
  ↓
Server creates session, stores in database
  ↓
Server sends session ID to user
  ↓
User sends session ID with every request
  ↓
Server queries database to validate session
```

**Problem:** Every request requires database lookup = slow

### The Modern Way: JWT

```
User logs in
  ↓
Server creates JWT token (contains user info)
  ↓
Server signs token with secret key
  ↓
User stores token, sends with every request
  ↓
Server validates signature (no database needed!)
```

**Benefits:**
- Fast (no database lookup)
- Stateless (server doesn't store anything)
- Scalable (works across multiple servers)

### JWT Structure

A JWT has 3 parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

└────────── header ──────────┘ └───────────── payload ────────────┘ └─────── signature ─────┘
```

**1. Header** (algorithm + type):
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**2. Payload** (user data):
```json
{
  "sub": "1234567890",  // User ID
  "email": "john@sjsu.edu",
  "exp": 1735689600  // Expiration timestamp
}
```

**3. Signature** (prevents tampering):
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

### How JWT Prevents Tampering

**User tries to change the payload:**

Original token:
```json
{"sub": "123", "email": "john@sjsu.edu"}
```

User edits it to:
```json
{"sub": "456", "email": "admin@sjsu.edu"}  // Trying to impersonate admin!
```

**What happens:**
1. User sends modified token
2. Server recalculates signature with SECRET_KEY
3. New signature ≠ old signature
4. **Server rejects token**: "Invalid signature"

**Security:** As long as SECRET_KEY is secret, tokens cannot be forged.

### Creating JWT in Our Code

**From `security.py:17`:**
```python
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

**Example:**
```python
# User logs in
user_id = 123
token = create_access_token(subject=user_id, expires_delta=timedelta(hours=24))
# Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# User sends token with request
# Server decodes it
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
print(payload["sub"])  # "123"
```

---

<a name="part5-4"></a>
## 24. OAuth2 Flow

### What is OAuth2?

OAuth2 is a **protocol** (set of rules) for authorization.

**Example you've seen:**
- "Sign in with Google"
- "Connect to Facebook"
- "Authorize GitHub"

### Our OAuth2 Flow

We use "OAuth2 with Password Flow" (simpler version):

```
1. User submits email + password
   POST /auth/login/access-token
   Body: {"username": "john@sjsu.edu", "password": "MyPassword123"}

2. Server validates credentials
   - Check email exists
   - Verify password hash
   - Check account is active

3. Server creates JWT token
   - Encode user ID in token
   - Set expiration (24 hours)
   - Sign with secret key

4. Server returns token
   Response: {"access_token": "eyJhbGc...", "token_type": "bearer"}

5. User stores token (localStorage, cookies)

6. User sends token with every request
   Header: Authorization: Bearer eyJhbGc...

7. Server validates token
   - Check signature
   - Check expiration
   - Extract user ID

8. Server processes request
   - Fetch user from database
   - Execute logic
   - Return response
```

### Code Example

**Login** (`auth.py:16`):
```python
@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1. Fetch user
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Verify password
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    # 3. Create token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
```

**Protected Route** (`deps.py:19`):
```python
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    # 1. Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    token_data = TokenData(**payload)

    # 2. Fetch user
    query = select(User).where(User.id == int(token_data.sub))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    return user
```

**Using it:**
```python
@app.get("/users/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user  # FastAPI automatically validates token!
```

---

<a name="part5-5"></a>
## 25. Protected Routes

### What are Protected Routes?

Routes that require authentication.

**Public routes:**
```python
@app.get("/health")  # Anyone can access
async def health_check():
    return {"status": "healthy"}
```

**Protected routes:**
```python
@app.get("/users/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user  # Must be logged in
```

### How It Works

**Without token:**
```bash
GET /users/me
```
Response:
```json
{
  "detail": "Not authenticated"
}
```

**With invalid token:**
```bash
GET /users/me
Authorization: Bearer invalid_token_12345
```
Response:
```json
{
  "detail": "Could not validate credentials"
}
```

**With valid token:**
```bash
GET /users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Response:
```json
{
  "id": 123,
  "email": "john@sjsu.edu",
  "full_name": "John Doe"
}
```

### Authorization vs Authentication

**Authentication**: "Who are you?" (login)
**Authorization**: "What can you do?" (permissions)

**Example:**
```python
# Authentication: User must be logged in
current_user = Depends(get_current_user)

# Authorization: User must be admin
if not current_user.is_admin:
    raise HTTPException(403, "Admin access required")
```

**Real-world example:**
```python
@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    # Authorization: Can only delete yourself (or if you're admin)
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized to delete this user")

    # Proceed with deletion
    ...
```

---

<a name="part5-6"></a>
## 26. CORS - Cross-Origin Resource Sharing

### The Problem

Your frontend and backend run on different origins:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`

By default, browsers **block** this for security:

```javascript
// Frontend tries to call API
fetch('http://localhost:8001/users/me')
// Browser blocks it: "CORS policy: No 'Access-Control-Allow-Origin' header"
```

### Why This Security Exists

**Scenario: Evil website**

You visit `evil.com` while logged into `bank.com`:

```javascript
// evil.com tries to steal your money
fetch('https://bank.com/api/transfer', {
  method: 'POST',
  body: JSON.stringify({to: 'hacker', amount: 1000})
})
```

**Without CORS:** Request succeeds, your money is gone
**With CORS:** Browser blocks the request

### The Solution: CORS Headers

Your backend tells the browser: "I trust localhost:3000"

**From `main.py:27`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**What this does:**

Backend adds headers to every response:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Allow-Credentials: true
```

Now browser allows the request.

### Production Settings

**Development:**
```python
ALLOWED_ORIGINS = ["http://localhost:3000", "*"]  # Allow everything
```

**Production:**
```python
ALLOWED_ORIGINS = [
    "https://sjsu-rideshare.com",  # Only your actual domain
]
```

**Security Rule: Never use `"*"` in production!**

---

# PART 6: DOCKER & CONTAINERIZATION

<a name="part6-1"></a>
## 27. What is Docker?

### The Problem Without Docker

**Developer 1's Machine:**
- Python 3.11
- PostgreSQL 15
- Redis 7
- macOS

**Developer 2's Machine:**
- Python 3.9
- PostgreSQL 14
- No Redis
- Windows

**Result:** "It works on my machine!" 😭

### The Solution: Containers

Docker packages your app + all dependencies into a **container**.

**Think of it like a shipping container:**
- Standard size
- Works on any ship (server)
- Contains everything needed
- Isolated from other containers

**Benefits:**
1. **Consistency**: Same environment everywhere (dev, staging, production)
2. **Isolation**: Each app has its own environment
3. **Portability**: Runs on any machine with Docker
4. **Easy Setup**: One command to start everything

### Docker vs Virtual Machines

**Virtual Machine:**
```
┌─────────────────────────────────────┐
│         Host Operating System        │
├─────────────────────────────────────┤
│           Hypervisor (VMware)        │
├──────────────┬──────────────────────┤
│   Guest OS   │     Guest OS         │
│   (2GB RAM)  │     (2GB RAM)        │
│ ┌──────────┐ │  ┌──────────┐        │
│ │   App 1  │ │  │   App 2  │        │
│ └──────────┘ │  └──────────┘        │
└──────────────┴──────────────────────┘
```

**Docker Container:**
```
┌─────────────────────────────────────┐
│         Host Operating System        │
├─────────────────────────────────────┤
│            Docker Engine             │
├──────────────┬──────────────────────┤
│  Container 1 │   Container 2        │
│  (100MB)     │   (100MB)            │
│ ┌──────────┐ │  ┌──────────┐        │
│ │   App 1  │ │  │   App 2  │        │
│ └──────────┘ │  └──────────┘        │
└──────────────┴──────────────────────┘
```

**Advantages:**
- Containers are **lightweight** (MBs vs GBs)
- Start **instantly** (seconds vs minutes)
- **More efficient** resource usage

---

<a name="part6-2"></a>
## 28. Containers vs Images

### Images

An **image** is like a recipe or blueprint:
- Read-only template
- Contains OS + dependencies + app code
- Stored as a file
- Can be shared (Docker Hub)

**Example:**
```
python:3.11-slim image contains:
- Debian Linux
- Python 3.11
- pip
- Basic libraries
```

### Containers

A **container** is a running instance of an image:
- Can read/write
- Has its own memory, CPU
- Isolated from other containers
- Can be started/stopped/deleted

**Analogy:**
- **Image** = Class (in programming)
- **Container** = Object/Instance

```python
# One image
class User:
    def __init__(self, name):
        self.name = name

# Many containers
user1 = User("Alice")  # Container 1
user2 = User("Bob")    # Container 2
user3 = User("Charlie") # Container 3
```

### Example

```bash
# Download image (once)
docker pull postgres:15-alpine

# Create containers (many times)
docker run postgres:15-alpine  # Container 1
docker run postgres:15-alpine  # Container 2

# Both containers run PostgreSQL, but are isolated
# Container 1's data ≠ Container 2's data
```

---

<a name="part6-3"></a>
## 29. Dockerfile Explained

### What is a Dockerfile?

A text file with instructions to build an image.

**Our Dockerfile** (`services/user-service/Dockerfile`):

```dockerfile
# 1. Base image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy application code
COPY . .

# 7. Expose port
EXPOSE 8000

# 8. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 9. Run command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Line-by-Line Explanation

**1. FROM python:3.11-slim**

Start with Python 3.11 base image (contains Linux + Python)

**2. WORKDIR /app**

Create `/app` directory and make it the current directory

**3. RUN apt-get...**

Install system packages:
- `gcc`: C compiler (needed for some Python packages)
- `postgresql-client`: PostgreSQL command-line tools

**4. COPY requirements.txt .**

Copy `requirements.txt` from your machine into the container

**Why separate step?**
- Docker caches each step
- If requirements don't change, Docker reuses cache
- Faster builds!

**5. RUN pip install...**

Install Python packages

**6. COPY . .**

Copy all your code into the container

**7. EXPOSE 8000**

Document that this container listens on port 8000
(Doesn't actually open the port, just documentation)

**8. HEALTHCHECK**

Every 30 seconds, Docker runs this command:
- If successful: Container is healthy
- If fails 3 times: Container is unhealthy

**9. CMD**

Default command to run when container starts:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Building an Image

```bash
# Build image
docker build -t user-service .

# Run container
docker run -p 8001:8000 user-service
```

---

<a name="part6-4"></a>
## 30. Docker Compose - Orchestration

### The Problem

Our app needs multiple services:
- User service (Python)
- PostgreSQL (Database)
- Redis (Cache)
- pgAdmin (Database UI)

**Running manually:**
```bash
docker run -d postgres
docker run -d redis
docker run -d user-service
docker run -d pgadmin
```

**Problems:**
- Tedious (4 commands)
- Services don't know about each other
- Hard to manage (start/stop/restart)

### The Solution: Docker Compose

One file + one command to manage everything.

**From `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  # Service 1: User Service
  user-service:
    build: ./services/user-service
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Service 2: PostgreSQL
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: rideshare
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s

  # Service 3: Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Service 4: pgAdmin
  pgadmin:
    image: dpage/pgadmin4
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@sjsu.edu
      PGADMIN_DEFAULT_PASSWORD: admin

networks:
  rideshare-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  pgadmin_data:
```

### Key Features

**1. Services**

Each service is a container:
- `user-service`: Your FastAPI app
- `postgres`: Database
- `redis`: Cache
- `pgadmin`: Database UI

**2. Ports**

```yaml
ports:
  - "8001:8000"
```

Maps port 8001 on your machine → port 8000 in container

**3. Environment Variables**

```yaml
environment:
  - DATABASE_URL=postgresql://...
```

Passed to the container

**4. Depends On**

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

Wait for PostgreSQL to be healthy before starting user-service

**5. Volumes**

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

Persist data even if container is deleted

**6. Networks**

All services are on same network, can talk to each other:

```python
# Inside user-service container, "postgres" resolves to postgres container
DATABASE_URL = "postgresql://postgres@postgres:5432/rideshare"
#                                      ^^^^^^^^ hostname
```

### Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f user-service

# Stop all services
docker-compose down

# Restart one service
docker-compose restart user-service

# Rebuild and restart
docker-compose up -d --build
```

---

<a name="part6-5"></a>
## 31. Volumes - Persistent Data

### The Problem

Containers are **ephemeral** (temporary):

```bash
# Start PostgreSQL container
docker run postgres

# Create database, add data
INSERT INTO users VALUES (...);

# Stop container
docker stop postgres

# Start container again
docker start postgres

# Data is GONE! 😭
```

### The Solution: Volumes

Volumes store data **outside** the container, on your host machine.

```yaml
services:
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      #   ^^^^^^^^^^^^^ volume name
      #                 ^^^^^^^^^^^^^^^^^^^^^^^^^ path inside container

volumes:
  postgres_data:
    driver: local
```

**How it works:**

```
Your Computer                    Container
┌────────────────┐              ┌────────────────┐
│                │              │                │
│  Docker Volume │ ←→ mounted → │ /var/lib/      │
│  postgres_data │              │ postgresql/    │
│                │              │ data           │
│  (permanent)   │              │  (temporary)   │
└────────────────┘              └────────────────┘
```

When container writes to `/var/lib/postgresql/data`, it's actually writing to the volume on your machine.

### Types of Volumes

**1. Named Volume (What we use):**
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

Docker manages the storage location.

**2. Bind Mount (For development):**
```yaml
volumes:
  - ./services/user-service/app:/app/app
```

Maps a folder on your machine → folder in container.
**Use case:** Hot reload (edit code on your machine, container sees changes)

**3. Anonymous Volume:**
```yaml
volumes:
  - /var/lib/postgresql/data
```

Docker creates a random volume (not recommended).

### Managing Volumes

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect postgres_data

# Remove volume (deletes data!)
docker volume rm postgres_data

# Remove all unused volumes
docker volume prune
```

---

<a name="part6-6"></a>
## 32. Networks - Container Communication

### The Problem

Containers are isolated:

```
Container 1 (user-service) → How to talk to Container 2 (postgres)?
```

### The Solution: Docker Networks

**From `docker-compose.yml:82`:**
```yaml
networks:
  rideshare-network:
    driver: bridge
```

All services join this network:
```yaml
services:
  user-service:
    networks:
      - rideshare-network

  postgres:
    networks:
      - rideshare-network
```

### How It Works

Docker creates a virtual network:

```
┌─────────────────────────────────────────┐
│       rideshare-network (172.18.0.0)    │
├─────────────────────────────────────────┤
│                                         │
│  user-service (172.18.0.2)              │
│  └→ Can reach: postgres, redis          │
│                                         │
│  postgres (172.18.0.3)                  │
│  └→ Can reach: user-service, redis      │
│                                         │
│  redis (172.18.0.4)                     │
│  └→ Can reach: user-service, postgres   │
│                                         │
└─────────────────────────────────────────┘
```

### DNS Resolution

Docker provides automatic DNS:

**Inside user-service container:**
```python
# "postgres" resolves to postgres container's IP
DATABASE_URL = "postgresql://postgres:5432/rideshare"

# "redis" resolves to redis container's IP
REDIS_URL = "redis://redis:6379/0"
```

No need to know IP addresses!

### Port Mapping

```yaml
user-service:
  ports:
    - "8001:8000"
```

**Two types of access:**

1. **From your machine:**
   ```bash
   curl http://localhost:8001/health
   ```

2. **From another container:**
   ```python
   # Inside another container
   requests.get("http://user-service:8000/health")
   #                   ^^^^^^^^^^^^^ container name
   #                               ^^^^ internal port
   ```

---

<a name="part6-7"></a>
## 33. Health Checks

### Why Health Checks?

**Problem:** Container is running, but app crashed

```bash
docker ps
# Shows: user-service is "Up"

# But actually:
curl http://localhost:8001/health
# Error: Connection refused

# Container is up, but app inside is dead!
```

### The Solution

**From `docker-compose.yml:39`:**
```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**What this does:**

Every 10 seconds, Docker runs:
```bash
pg_isready -U postgres
```

- If successful: Container is **healthy** ✅
- If fails 5 times: Container is **unhealthy** ❌

### Using Health Checks

**From `docker-compose.yml:19`:**
```yaml
user-service:
  depends_on:
    postgres:
      condition: service_healthy
```

**This means:**
- Don't start user-service until PostgreSQL is healthy
- Prevents "Can't connect to database" errors on startup

### Monitoring Health

```bash
# Check status
docker ps
# Shows: user-service (healthy)

# View health check logs
docker inspect user-service | grep -A 10 Health
```

**Logs show:**
```json
{
  "Status": "healthy",
  "FailingStreak": 0,
  "Log": [
    {
      "Start": "2024-12-20T10:00:00Z",
      "End": "2024-12-20T10:00:00Z",
      "ExitCode": 0,
      "Output": "accepting connections"
    }
  ]
}
```

---

# PART 7: ARCHITECTURE

<a name="part7-1"></a>
## 34. Monolithic vs Microservices

### Monolithic Architecture

**One big application:**

```
┌──────────────────────────────────────┐
│         RideShare Application        │
├──────────────────────────────────────┤
│  UserController                      │
│  RideController                      │
│  BookingController                   │
│  PaymentController                   │
│  NotificationController              │
├──────────────────────────────────────┤
│         Shared Database              │
└──────────────────────────────────────┘
```

**Pros:**
- Simple to develop
- Easy to test
- Simple deployment

**Cons:**
- Hard to scale (must scale entire app)
- One bug can crash everything
- Long deployment times
- Hard to update (must redeploy everything)

### Microservices Architecture

**Multiple small applications:**

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ User Service │  │ Ride Service │  │Book Service  │
│ Port: 8001   │  │ Port: 8002   │  │ Port: 8003   │
├──────────────┤  ├──────────────┤  ├──────────────┤
│  PostgreSQL  │  │  PostgreSQL  │  │  PostgreSQL  │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐
│ Payment Svc  │  │ Notify Svc   │
│ Port: 8004   │  │ Port: 8005   │
├──────────────┤  ├──────────────┤
│  PostgreSQL  │  │    Redis     │
└──────────────┘  └──────────────┘
```

**Pros:**
- Independent scaling (scale payment service separately)
- Fault isolation (payment fails, rides still work)
- Independent deployment (update user service without touching others)
- Technology flexibility (different languages per service)

**Cons:**
- Complex (need to manage multiple services)
- Network latency (services talk over HTTP)
- Data consistency challenges
- Harder to debug

---

<a name="part7-2"></a>
## 35. Why Microservices for RideShare?

### Our Services

**1. User Service (Port 8001)**
- User registration/login
- Profile management
- Authentication
- **Load:** Steady (every request needs auth)

**2. Ride Service (Port 8002)**
- Post rides
- Search rides
- View ride details
- **Load:** Medium (lots of searches)

**3. Booking Service (Port 8003)**
- Request booking
- Approve/reject
- Manage seats
- **Load:** High (critical path)

**4. Notification Service (Port 8004)**
- Send emails
- Push notifications
- SMS (future)
- **Load:** Spiky (bulk sends)

**5. Tracking Service (Port 8005)**
- Real-time location
- WebSocket connections
- Route tracking
- **Load:** Very High (constant updates)

### Why This Makes Sense

**Scenario 1: Black Friday Sale**

Rides spike 10x:
- Scale only Ride Service (add more containers)
- Don't need to scale User Service

**Scenario 2: Notification Failure**

Email service is down:
- Users can still book rides
- Critical functionality works
- Fix notification service separately

**Scenario 3: Performance Optimization**

Tracking needs to be fast:
- Write tracking service in Go (faster than Python)
- Other services stay in Python
- Mix and match technologies

**Scenario 4: Team Organization**

5 developers:
- Alice: User Service
- Bob: Ride Service
- Charlie: Booking Service
- Diana: Notification Service
- Eve: Tracking Service

Everyone works independently, no merge conflicts.

---

<a name="part7-3"></a>
## 36. Service Communication Patterns

### Synchronous Communication (HTTP/REST)

**How it works:**

```
Booking Service needs to send notification
  ↓
POST http://notification-service:8004/send-email
  ↓
Wait for response
  ↓
Response: {"status": "sent"}
```

**Code example:**
```python
# In booking service
import httpx

async def create_booking(booking_data):
    # 1. Save booking to database
    booking = Booking(**booking_data)
    db.add(booking)
    await db.commit()

    # 2. Send notification (synchronous call)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://notification-service:8004/send-email",
            json={
                "to": booking.user.email,
                "subject": "Booking Confirmed",
                "body": f"Your booking #{booking.id} is confirmed"
            }
        )

    # 3. Wait for response
    if response.status_code != 200:
        # Handle error
        logger.error("Failed to send notification")

    return booking
```

**Pros:**
- Simple
- Immediate response
- Easy to debug

**Cons:**
- Blocking (booking service waits for notification)
- Tight coupling
- Cascading failures (if notification is down, booking fails)

### Asynchronous Communication (Message Queue)

**How it works:**

```
Booking Service publishes message
  ↓
Message Queue (RabbitMQ/Redis)
  ↓
Notification Service subscribes and processes
```

**Code example:**
```python
# In booking service
async def create_booking(booking_data):
    # 1. Save booking to database
    booking = Booking(**booking_data)
    db.add(booking)
    await db.commit()

    # 2. Publish event (fire and forget)
    await redis.publish(
        "booking.created",
        json.dumps({
            "booking_id": booking.id,
            "user_email": booking.user.email
        })
    )

    # 3. Return immediately (don't wait)
    return booking

# In notification service (separate process)
async def listen_for_bookings():
    pubsub = redis.pubsub()
    pubsub.subscribe("booking.created")

    async for message in pubsub.listen():
        data = json.loads(message["data"])
        await send_email(data["user_email"], "Booking Confirmed")
```

**Pros:**
- Non-blocking (booking completes faster)
- Loose coupling
- Fault tolerance (if notification fails, booking still succeeds)
- Retry logic (queue can retry failed messages)

**Cons:**
- More complex
- Eventual consistency (notification sent later)
- Harder to debug

### Our Strategy

**For RideShare:**

**Use Synchronous for:**
- Critical operations (payment processing)
- Immediate responses needed (user profile)
- Simple workflows

**Use Asynchronous for:**
- Non-critical operations (notifications)
- Bulk operations (send 1000 emails)
- Long-running tasks (generating reports)

---

<a name="part7-4"></a>
## 37. Project Structure Best Practices

### Our Structure

```
RideShare/
├── backend/
│   ├── services/
│   │   ├── user-service/
│   │   │   ├── app/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── main.py           # Entry point
│   │   │   │   ├── api/              # API routes
│   │   │   │   │   ├── routes/
│   │   │   │   │   │   ├── auth.py   # /auth/login
│   │   │   │   │   │   ├── users.py  # /users/me
│   │   │   │   │   │   └── health.py # /health
│   │   │   │   ├── core/             # Core functionality
│   │   │   │   │   ├── config.py     # Settings
│   │   │   │   │   └── security.py   # JWT, hashing
│   │   │   │   ├── db/               # Database
│   │   │   │   │   ├── base.py       # Base class
│   │   │   │   │   └── session.py    # Session factory
│   │   │   │   ├── models/           # Database models
│   │   │   │   │   └── user.py       # User table
│   │   │   │   ├── schemas/          # Pydantic schemas
│   │   │   │   │   └── user.py       # Validation
│   │   │   │   └── middleware/       # Middleware
│   │   │   │       ├── logging_middleware.py
│   │   │   │       └── error_handler.py
│   │   │   ├── tests/                # Tests
│   │   │   ├── Dockerfile            # Container definition
│   │   │   ├── requirements.txt      # Dependencies
│   │   │   └── .env                  # Environment vars
│   │   ├── ride-service/             # Same structure
│   │   ├── booking-service/
│   │   └── notification-service/
│   └── docker-compose.yml            # Orchestration
├── mobile/                           # React Native app
├── docs/                             # Documentation
└── README.md
```

### Why This Structure?

**1. Separation of Concerns**

Each folder has ONE job:
- `api/`: HTTP endpoints
- `core/`: Business logic
- `db/`: Database connections
- `models/`: Data structures
- `schemas/`: Validation

**2. Scalability**

Easy to find things:
- Need to add a new route? → `api/routes/`
- Need to change JWT logic? → `core/security.py`
- Need to add a field to User? → `models/user.py`

**3. Testability**

```python
# Test database logic without running the server
from app.models.user import User

def test_user_creation():
    user = User(email="test@sjsu.edu")
    assert user.email == "test@sjsu.edu"
```

**4. Reusability**

```python
# Share security functions across services
from app.core.security import create_access_token

# Used in auth.py, users.py, admin.py, etc.
```

---

# PART 8: DEVELOPMENT WORKFLOW

<a name="part8-1"></a>
## 38. Environment Variables

### Why Environment Variables?

**Bad (hardcoding):**
```python
DATABASE_URL = "postgresql://postgres:mypassword@localhost:5432/rideshare"
SECRET_KEY = "super_secret_key_12345"
```

**Problems:**
1. Secrets in code (can't share on GitHub)
2. Different values for dev/prod
3. Hard to change (need to edit code)

**Good (environment variables):**
```python
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
```

### Using .env Files

**Create `.env`:**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rideshare
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=my_super_secret_key
DEBUG=True
```

**Load in Python** (`config.py:4`):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

Pydantic automatically reads `.env` and validates types.

### Different Environments

**.env.development:**
```env
DATABASE_URL=postgresql://localhost:5432/rideshare_dev
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000
```

**.env.production:**
```env
DATABASE_URL=postgresql://prod-server:5432/rideshare
DEBUG=False
ALLOWED_ORIGINS=https://sjsu-rideshare.com
SECRET_KEY=very_long_random_string_from_secure_generator
```

### Security Rules

1. **Never commit .env to Git**
   ```gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Use .env.example as template**
   ```env
   # .env.example (safe to commit)
   DATABASE_URL=postgresql://user:password@localhost:5432/db
   SECRET_KEY=change_this_in_production
   ```

3. **Generate strong secrets**
   ```bash
   # Generate random secret key
   openssl rand -hex 32
   ```

---

<a name="part8-2"></a>
## 39. Logging Best Practices

### Why Logging?

**Without logs:**
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.query(User).get(user_id)
    return user

# Something goes wrong...
# You have no idea what happened 😭
```

**With logs:**
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    logger.info(f"Fetching user {user_id}")

    try:
        user = db.query(User).get(user_id)
        logger.info(f"User {user_id} found")
        return user
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise
```

**Logs:**
```
2024-12-20 10:00:00 - INFO - Fetching user 123
2024-12-20 10:00:00 - ERROR - Failed to fetch user 123: Database connection failed
```

Now you know exactly what went wrong!

### Log Levels

```python
logger.debug("Detailed debugging info")     # Only in development
logger.info("Normal operations")            # General info
logger.warning("Something unexpected")      # Potential issues
logger.error("Something failed")            # Errors
logger.critical("System is broken")         # Severe errors
```

**Example:**
```python
logger.debug(f"SQL Query: {query}")  # Too verbose for production
logger.info("User logged in")        # Useful in production
logger.warning("Slow query detected") # Needs attention
logger.error("Payment failed")       # Immediate action needed
logger.critical("Database is down")  # WAKE UP THE ENGINEER
```

### Our Logging Setup

**From `main.py:10`:**
```python
logging.basicConfig(
    level=settings.LOG_LEVEL,  # INFO, DEBUG, etc.
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**Output:**
```
2024-12-20 10:00:00,123 - app.main - INFO - Starting user-service...
2024-12-20 10:00:01,456 - app.api.routes.auth - INFO - User john@sjsu.edu logged in
2024-12-20 10:00:02,789 - app.middleware.logging_middleware - INFO - GET /health - 200 - 45.23ms
```

### What to Log

**DO log:**
- Request start/end (with timing)
- User actions (login, register, booking)
- External API calls
- Errors and exceptions
- Important state changes

**DON'T log:**
- Passwords (NEVER!)
- Credit card numbers
- Full user data (privacy)
- Every database query (too verbose)

**Example:**
```python
# Good
logger.info(f"User {user.id} created booking")

# Bad
logger.info(f"User {user.email} with password {user.password} created booking")
#                                              ^^^^^^^^^^^^^^ NEVER!
```

---

<a name="part8-3"></a>
## 40. Error Handling

### The Problem

**No error handling:**
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.query(User).get(user_id)  # What if user doesn't exist?
    return user  # Returns None → JSON response: null 😕
```

### HTTP Exception

**From `auth.py:32`:**
```python
if not user or not security.verify_password(form_data.password, user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )
```

**Response:**
```json
{
  "detail": "Incorrect email or password"
}
```

Status code: 401 (Unauthorized)

### Global Exception Handler

**From `error_handler.py:10`:**
```python
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exception
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())

    # Create error response
    error_response = {
        "error": type(exc).__name__,
        "message": "An internal error occurred",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": str(request.url)
    }

    # Include details in debug mode
    if settings.DEBUG:
        error_response["detail"] = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )
```

**What this does:**

Any unhandled exception becomes a nice JSON response:

**Development (DEBUG=True):**
```json
{
  "error": "ValueError",
  "message": "An internal error occurred",
  "detail": "invalid literal for int() with base 10: 'abc'",
  "timestamp": "2024-12-20T10:00:00Z",
  "path": "/users/abc"
}
```

**Production (DEBUG=False):**
```json
{
  "error": "ValueError",
  "message": "An internal error occurred",
  "timestamp": "2024-12-20T10:00:00Z",
  "path": "/users/abc"
}
```

(No `detail` field → don't expose internal errors to users)

---

<a name="part8-4"></a>
## 41. Hot Reloading

### What is Hot Reloading?

**Without hot reload:**
1. Edit code
2. Stop server
3. Restart server
4. Test changes

**With hot reload:**
1. Edit code
2. Server automatically restarts
3. Test changes

**Saves hours of time!**

### How We Enable It

**From `Dockerfile:31`:**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#                                                                        ^^^^^^^^
```

**From `docker-compose.yml:16`:**
```yaml
user-service:
  volumes:
    - ./services/user-service/app:/app/app  # Bind mount
```

**How it works:**

1. Your code is on your machine: `./services/user-service/app`
2. Docker maps it to container: `/app/app`
3. You edit a file on your machine
4. Change is immediately visible in container
5. Uvicorn detects change
6. Uvicorn restarts app

**Logs:**
```
INFO:     Will watch for changes in these directories: ['/app']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Edit `health.py`:
```
WARNING:  Detected file change in 'app/api/routes/health.py'. Reloading...
INFO:     Application shutdown.
INFO:     Application startup complete.
```

**Takes ~1 second instead of manually restarting!**

---

<a name="part8-5"></a>
## 42. Testing Basics

### Why Testing?

**Without tests:**
1. Make a change
2. Manually test every feature
3. Hope nothing broke
4. Deploy
5. User reports bug 😭

**With tests:**
1. Make a change
2. Run tests (automated)
3. Tests pass → confident to deploy
4. Tests fail → caught the bug before users did!

### Types of Tests

**1. Unit Tests**
Test individual functions

```python
def test_password_hashing():
    password = "MyPassword123"
    hashed = get_password_hash(password)

    # Should be different
    assert hashed != password

    # Should verify correctly
    assert verify_password(password, hashed) == True

    # Wrong password should fail
    assert verify_password("WrongPassword", hashed) == False
```

**2. Integration Tests**
Test how components work together

```python
async def test_user_registration():
    # Create user
    response = client.post("/auth/register", json={
        "email": "test@sjsu.edu",
        "password": "Password123!",
        "full_name": "Test User"
    })
    assert response.status_code == 201

    # Verify user exists in database
    user = await db.execute(select(User).where(User.email == "test@sjsu.edu"))
    user = user.scalar_one()
    assert user is not None
    assert user.full_name == "Test User"
```

**3. End-to-End Tests**
Test entire user flows

```python
async def test_booking_flow():
    # 1. Register user
    register_response = client.post("/auth/register", ...)

    # 2. Login
    login_response = client.post("/auth/login", ...)
    token = login_response.json()["access_token"]

    # 3. Create ride
    ride_response = client.post("/rides", headers={"Authorization": f"Bearer {token}"}, ...)

    # 4. Book ride
    booking_response = client.post("/bookings", headers={"Authorization": f"Bearer {token}"}, ...)

    # 5. Verify booking
    assert booking_response.status_code == 201
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app

# Run with verbose output
pytest -v
```

---

# PART 9: FILE-BY-FILE CODE WALKTHROUGH

<a name="part9-1"></a>
## 43. Understanding main.py

**Full file:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import health

# 1. Setup Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2. Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User management and authentication service for SJSU RideShare",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3. Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Middleware & Error Handlers
from app.middleware.logging_middleware import logging_middleware
from app.middleware.error_handler import global_exception_handler

app.middleware("http")(logging_middleware)
app.add_exception_handler(Exception, global_exception_handler)

# 5. Include Routers
app.include_router(health.router, tags=["Health"])
from app.api.routes import auth, users
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])

# 6. Startup Event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.SERVICE_NAME}...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
```

### Line-by-Line

**Lines 1-5: Imports**
- `FastAPI`: The framework
- `CORSMiddleware`: Cross-origin resource sharing
- `logging`: For logging
- `settings`: Our configuration

**Lines 8-13: Logging Setup**
- `basicConfig`: Configure Python's logging system
- `level=settings.LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR from .env
- `format`: How logs look
- `getLogger(__name__)`: Get logger for this file

**Lines 16-23: Create FastAPI App**
- `title`: Shows in /docs
- `description`: API description
- `version`: API version
- `docs_url="/docs"`: Swagger UI at http://localhost:8001/docs
- `redoc_url="/redoc"`: ReDoc at http://localhost:8001/redoc

**Lines 26-32: CORS Middleware**
- `allow_origins`: Which websites can call our API
- `allow_credentials=True`: Allow cookies
- `allow_methods=["*"]`: Allow GET, POST, PUT, DELETE
- `allow_headers=["*"]`: Allow all headers

**Lines 35-39: Custom Middleware**
- `logging_middleware`: Logs every request
- `global_exception_handler`: Catches all errors

**Lines 42-45: Include Routers**
- `health.router`: /health endpoint
- `auth.router`: /api/v1/auth/* endpoints
- `users.router`: /api/v1/users/* endpoints

**Lines 48-53: Lifecycle Events**
- `startup`: Runs once when server starts
- `shutdown`: Runs once when server stops

---

<a name="part9-2"></a>
## 44. Understanding config.py

**Full file:**
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Service Info
    SERVICE_NAME: str = "user-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database Configuration
    DATABASE_URL: str
    REDIS_URL: str

    # Security
    SECRET_KEY: str = "temporary_secret_key_for_dev_only_change_in_prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SJSU RideShare"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### How It Works

**1. Pydantic BaseSettings**

Automatically reads from environment variables and .env file.

**2. Type Validation**

```python
DEBUG: bool = False
```

If you set `DEBUG=yes` in .env:
- Pydantic converts "yes" → True

If you set `ACCESS_TOKEN_EXPIRE_MINUTES=hello`:
- Pydantic crashes: "Cannot convert to int"

**3. Default Values**

```python
LOG_LEVEL: str = "INFO"
```

If not in .env, uses "INFO"

**4. Required Fields**

```python
DATABASE_URL: str  # No default = required
```

If missing from .env, app crashes on startup.

**5. Usage**

```python
from app.core.config import settings

print(settings.DATABASE_URL)
print(settings.DEBUG)
```

---

<a name="part9-3"></a>
## 45. Understanding models/user.py

**Full file:**
```python
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Generated SQL

SQLAlchemy creates this table:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    phone_number VARCHAR UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_full_name ON users(full_name);
CREATE INDEX ix_users_phone_number ON users(phone_number);
```

### Field-by-Field

**id:**
- Primary key (unique identifier)
- Integer
- Auto-incrementing (1, 2, 3, ...)
- Indexed (fast lookups)

**email:**
- String
- Unique (no duplicate emails)
- Indexed (fast login by email)
- Not null (required)

**hashed_password:**
- String
- Never store plain passwords!
- Not null

**full_name:**
- String
- Optional (can be null)
- Indexed (search by name)

**phone_number:**
- String
- Unique
- Optional

**is_active:**
- Boolean
- Default: True
- Used to soft-delete users

**created_at:**
- Timestamp with timezone
- Automatically set by database (server_default)

**updated_at:**
- Timestamp
- Automatically updated on every change (onupdate)

---

<a name="part9-4"></a>
## 46. Understanding schemas/user.py

**Full file:**
```python
from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
```

### Purpose

Schemas define:
1. What data can come IN (UserCreate)
2. What data goes OUT (UserResponse)
3. Validation rules

### Schemas Explained

**Token:**
```python
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**UserCreate (Registration):**
```python
{
  "email": "john@sjsu.edu",
  "password": "MyPassword123!",
  "full_name": "John Doe",
  "phone_number": "4081234567"
}
```

**UserResponse (What user sees):**
```python
{
  "id": 123,
  "email": "john@sjsu.edu",
  "full_name": "John Doe",
  "phone_number": "4081234567",
  "is_active": true
}
```

**Note:** No `password` or `hashed_password` in response!

### Validation

```python
email: EmailStr
```

Pydantic validates:
```python
# Valid
UserCreate(email="john@sjsu.edu", ...)  ✓

# Invalid
UserCreate(email="not-an-email", ...)  ✗
# Error: "value is not a valid email address"
```

---

<a name="part9-5"></a>
## 47. Understanding security.py

**Full file:**
```python
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Functions

**1. create_access_token()**

Creates JWT token:

```python
token = create_access_token(
    subject=user.id,
    expires_delta=timedelta(hours=24)
)
# Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Token payload:
```json
{
  "sub": "123",  // User ID
  "exp": 1735689600  // Expiration timestamp
}
```

**2. get_password_hash()**

Hashes password:

```python
hashed = get_password_hash("MyPassword123")
# Returns: "$2b$12$abcdefghijklmnopqrstuvwxyz..."
```

**3. verify_password()**

Checks if password matches hash:

```python
is_valid = verify_password("MyPassword123", user.hashed_password)
# Returns: True or False
```

---

<a name="part9-6"></a>
## 48. Understanding deps.py

**Full file:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenData
from sqlalchemy.future import select

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login/access-token"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenData(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(403, "Could not validate credentials")

    query = select(User).where(User.id == int(token_data.sub))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    if not user.is_active:
        raise HTTPException(400, "Inactive user")

    return user
```

### How It Works

**1. OAuth2PasswordBearer**

Tells FastAPI to extract token from header:

```
Authorization: Bearer eyJhbGc...
                      ^^^^^^^^ Extract this
```

**2. get_current_user()**

**Step 1:** Decode token
```python
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
# {"sub": "123", "exp": 1735689600}
```

**Step 2:** Extract user ID
```python
token_data = TokenData(**payload)
user_id = token_data.sub  # "123"
```

**Step 3:** Fetch user from database
```python
query = select(User).where(User.id == int(user_id))
result = await db.execute(query)
user = result.scalar_one_or_none()
```

**Step 4:** Validate
```python
if not user:
    raise HTTPException(404, "User not found")

if not user.is_active:
    raise HTTPException(400, "Inactive user")
```

**Step 5:** Return user
```python
return user
```

### Usage

```python
@app.get("/users/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

FastAPI automatically:
1. Extracts token from header
2. Calls get_current_user(token)
3. Passes result to your function

---

<a name="part9-7"></a>
## 49. Understanding routes/auth.py

**Full file:**
```python
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1. Fetch User by Email
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Authenticate
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    if not user.is_active:
        raise HTTPException(400, "Inactive user")

    # 3. Create Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
```

### Login Flow

**Request:**
```
POST /api/v1/auth/login/access-token
Content-Type: application/x-www-form-urlencoded

username=john@sjsu.edu&password=MyPassword123
```

**Step 1: Find User**
```python
query = select(User).where(User.email == form_data.username)
result = await db.execute(query)
user = result.scalar_one_or_none()
```

**Step 2: Verify Password**
```python
if not user or not security.verify_password(form_data.password, user.hashed_password):
    raise HTTPException(401, "Incorrect email or password")
```

**Step 3: Create Token**
```python
access_token = security.create_access_token(
    subject=user.id,
    expires_delta=timedelta(minutes=30)
)
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

# PART 10: COMMON QUESTIONS & TROUBLESHOOTING

<a name="part10-1"></a>
## 50. FAQ

### Q1: What's the difference between async and sync?

**Sync:** Waits for each operation to finish
```python
def get_data():
    data1 = fetch_from_db()  # Wait 100ms
    data2 = fetch_from_api()  # Wait 100ms
    return data1, data2  # Total: 200ms
```

**Async:** Can do multiple things at once
```python
async def get_data():
    data1 = await fetch_from_db()  # Start, don't wait
    data2 = await fetch_from_api()  # Start, don't wait
    # While waiting, server handles other requests
    return data1, data2  # Total: still 200ms, but server not blocked
```

### Q2: Why use Docker instead of running Python directly?

**Without Docker:**
- "Works on my machine"
- Different Python versions
- Missing dependencies
- Hard to deploy

**With Docker:**
- Same environment everywhere
- All dependencies included
- Easy deployment (just run container)

### Q3: What's the difference between a database and a cache?

**Database (PostgreSQL):**
- Permanent storage
- Slower (disk)
- Complex queries
- Reliable

**Cache (Redis):**
- Temporary storage
- Very fast (RAM)
- Simple lookups
- Data can be lost

**Use both:** PostgreSQL for permanent data, Redis for speed.

### Q4: Why not store passwords in plain text?

If database is hacked:
- Hacker has everyone's passwords
- Can login as anyone
- Most people reuse passwords → access to their other accounts

**Always hash passwords!**

### Q5: What's the difference between authentication and authorization?

**Authentication:** "Who are you?"
- Login with email/password
- Proves identity

**Authorization:** "What can you do?"
- Admin can delete users
- Regular user cannot
- Defines permissions

---

<a name="part10-2"></a>
## 51. Common Errors and Solutions

### Error 1: "Cannot connect to Docker daemon"

**Cause:** Docker Desktop not running

**Solution:**
```bash
# Mac/Windows: Start Docker Desktop application
# Linux:
sudo systemctl start docker
```

### Error 2: "Port 5432 already in use"

**Cause:** PostgreSQL already running on your machine

**Solution:**
```bash
# Option 1: Stop local PostgreSQL
brew services stop postgresql

# Option 2: Change port in docker-compose.yml
ports:
  - "5433:5432"  # Use 5433 instead
```

### Error 3: "ModuleNotFoundError: No module named 'app'"

**Cause:** Wrong directory or import path

**Solution:**
```bash
# Make sure you're in the right directory
cd backend/services/user-service

# Check PYTHONPATH
export PYTHONPATH=/app
```

### Error 4: "Could not validate credentials"

**Cause:** Invalid or expired JWT token

**Solution:**
- Login again to get fresh token
- Check SECRET_KEY matches
- Check token expiration time

### Error 5: "Database connection failed"

**Cause:** PostgreSQL not ready or wrong URL

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check health
docker-compose logs postgres

# Verify URL in .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rideshare
```

---

<a name="part10-3"></a>
## 52. Next Steps

### What You've Learned

You now understand:
✅ FastAPI and Python web development
✅ Docker and containerization
✅ PostgreSQL and SQLAlchemy
✅ Redis and caching
✅ JWT authentication
✅ Microservices architecture
✅ REST APIs
✅ Async programming

### What's Next?

**Section 2:** (Already implemented!)
- User registration
- Login/logout
- Profile management

**Section 3-4:** Ride Service
- Post rides
- Search rides
- Google Maps integration

**Section 5:** Smart Matching Algorithm
- ML-based ride matching
- Preference scoring

**Section 6:** Booking Service
- Request bookings
- Approve/reject
- Seat management

**Section 7:** Notifications
- Email notifications
- Push notifications
- SendGrid integration

**Section 8:** Real-time Tracking
- WebSocket connections
- Live location updates

**Section 9:** Payments
- Stripe integration
- Payment processing

**Section 10-13:** Testing & Deployment
- Comprehensive tests
- CI/CD pipeline
- Deploy to Railway

### Resources for Learning More

**FastAPI:**
- Official docs: https://fastapi.tiangolo.com
- Tutorial: https://fastapi.tiangolo.com/tutorial/

**SQLAlchemy:**
- Docs: https://docs.sqlalchemy.org
- Async tutorial: https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html

**Docker:**
- Get started: https://docs.docker.com/get-started/
- Best practices: https://docs.docker.com/develop/dev-best-practices/

**Python:**
- Async/await: https://realpython.com/async-io-python/
- Type hints: https://docs.python.org/3/library/typing.html

---

# Congratulations!

You've completed the comprehensive technology guide for RideShare! You now have a solid understanding of every technology in our stack.

Keep this document as reference. As you continue building, refer back to these concepts whenever you need clarification.

**Happy coding!** 🚀
