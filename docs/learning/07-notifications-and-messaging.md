# Section 7: Notifications and Messaging - Complete Learning Guide

**SJSU RideShare Development Series**
**Author:** Claude Code
**Date:** January 2026
**Prerequisites:** Sections 1-6 completed

---

## Table of Contents

1. [Introduction to Notification Systems](#1-introduction-to-notification-systems)
2. [Email Notifications with SendGrid](#2-email-notifications-with-sendgrid)
3. [Push Notifications with Firebase](#3-push-notifications-with-firebase)
4. [Email Templates with Jinja2](#4-email-templates-with-jinja2)
5. [User Notification Preferences](#5-user-notification-preferences)
6. [Notification Delivery Architecture](#6-notification-delivery-architecture)
7. [Error Handling and Resilience](#7-error-handling-and-resilience)
8. [Deep Linking and Mobile Integration](#8-deep-linking-and-mobile-integration)
9. [Best Practices for Notifications](#9-best-practices-for-notifications)
10. [Testing Notification Systems](#10-testing-notification-systems)
11. [Production Considerations](#11-production-considerations)
12. [Summary and Key Takeaways](#12-summary-and-key-takeaways)

---

## 1. Introduction to Notification Systems

### What Are Notifications?

Notifications are messages sent to users to inform them about important events in your application. In RideShare, notifications keep users informed about:

- New ride requests
- Booking approvals/rejections
- Ride reminders
- Payment confirmations
- Reviews and ratings

### Why Multiple Channels?

We use both **email** and **push notifications** because:

1. **Email**
   - Permanent record users can search later
   - Works on all devices
   - No app installation required
   - Good for detailed information
   - Professional and formal

2. **Push Notifications**
   - Instant delivery
   - High visibility (appears on lock screen)
   - Better engagement rates
   - Good for time-sensitive alerts
   - Requires app installation

3. **Both Together**
   - Redundancy ensures delivery
   - Users can choose their preference
   - Different use cases for each channel

### Notification Service Architecture

```
┌─────────────────┐
│ Booking Service │ ──┐
└─────────────────┘   │
                      │
┌─────────────────┐   │    ┌──────────────────────┐
│  Ride Service   │ ──┼───→│ Notification Service │
└─────────────────┘   │    └──────────────────────┘
                      │             │
┌─────────────────┐   │             ├─→ SendGrid (Email)
│ Payment Service │ ──┘             │
└─────────────────┘                 └─→ Firebase (Push)
```

**Key Principle:** Notification service is a separate microservice that other services call when they need to notify users.

---

## 2. Email Notifications with SendGrid

### What is SendGrid?

SendGrid is an email delivery platform that handles the complex infrastructure of sending emails reliably.

**Why not use standard SMTP?**
- SMTP emails often go to spam
- No delivery tracking
- IP reputation management is complex
- No analytics or metrics
- Rate limiting issues

**SendGrid provides:**
- High deliverability (avoids spam)
- Delivery tracking and analytics
- Template management
- API-based sending (easier than SMTP)
- Free tier: 100 emails/day

### Setting Up SendGrid

#### Step 1: Create Account

```bash
# 1. Go to https://sendgrid.com
# 2. Sign up for free account
# 3. Verify email address
```

#### Step 2: Create API Key

```bash
# In SendGrid dashboard:
Settings → API Keys → Create API Key

# Select "Full Access" for development
# Copy the key (you can't see it again!)
```

#### Step 3: Verify Sender Email

```bash
# In SendGrid dashboard:
Settings → Sender Authentication → Verify Single Sender

# Enter:
From Name: SJSU RideShare
From Email: noreply@sjsurideshare.com

# For production, you'll need to own the domain
```

#### Step 4: Configure Environment

```bash
# .env file
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@sjsurideshare.com
SENDGRID_FROM_NAME=SJSU RideShare
```

### SendGrid Python Integration

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Initialize client
sg = SendGridAPIClient(api_key)

# Create email
message = Mail(
    from_email=('noreply@sjsurideshare.com', 'SJSU RideShare'),
    to_emails='passenger@example.com',
    subject='Ride Approved!',
    html_content='<h1>Your ride has been approved!</h1>'
)

# Send
response = sg.send(message)

# Check status
if response.status_code in [200, 201, 202]:
    print("Email sent successfully!")
```

### Understanding SendGrid Response Codes

```python
200 - OK (sent successfully)
202 - Accepted (queued for delivery)
400 - Bad Request (check email format)
401 - Unauthorized (check API key)
429 - Too Many Requests (rate limit exceeded)
```

### SendGrid Best Practices

1. **Always Handle Failures Gracefully**
   ```python
   try:
       response = sg.send(message)
       return True
   except Exception as e:
       logger.error(f"Email failed: {e}")
       return False  # Don't crash the app!
   ```

2. **Monitor Your Quota**
   - Free tier: 100 emails/day
   - Track usage in dashboard
   - Implement rate limiting if needed

3. **Keep Emails Out of Spam**
   - Use verified sender email
   - Include unsubscribe link
   - Don't use spam trigger words
   - Maintain clean HTML structure

---

## 3. Push Notifications with Firebase

### What is Firebase Cloud Messaging (FCM)?

Firebase Cloud Messaging is Google's free platform for sending push notifications to mobile devices (Android and iOS).

### How Push Notifications Work

```
1. User opens app on their phone
2. App registers with Firebase → Gets FCM token
3. App sends FCM token to your backend
4. Backend stores token in user profile
5. When event occurs:
   - Backend calls Firebase API with token
   - Firebase delivers to user's device
   - Notification appears on lock screen
```

### Setting Up Firebase

#### Step 1: Create Firebase Project

```bash
# 1. Go to https://console.firebase.google.com
# 2. Click "Create Project"
# 3. Name: SJSU-RideShare
# 4. Disable analytics (optional for dev)
```

#### Step 2: Add Apps

```bash
# For Android:
Project Settings → Add App → Android
Package name: com.sjsu.rideshare

# For iOS:
Project Settings → Add App → iOS
Bundle ID: com.sjsu.rideshare

# Download google-services.json (Android)
# Download GoogleService-Info.plist (iOS)
```

#### Step 3: Generate Service Account

```bash
# In Firebase Console:
Project Settings → Service Accounts → Generate New Private Key

# Download firebase-credentials.json
# Store securely (DO NOT commit to git!)
```

#### Step 4: Configure Environment

```bash
# .env file
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FIREBASE_ENABLED=True
```

### Firebase Python Integration

```python
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize (do this once at startup)
cred = credentials.Certificate('firebase-credentials.json')
firebase_admin.initialize_app(cred)

# Send notification
message = messaging.Message(
    notification=messaging.Notification(
        title='Ride Approved!',
        body='Your ride to San Jose has been confirmed'
    ),
    data={
        'booking_id': '123',
        'type': 'booking_approved',
        'route': 'deeplink://booking/123'
    },
    token=user_fcm_token
)

response = messaging.send(message)
print(f"Successfully sent: {response}")
```

### FCM Token Management

**Important:** FCM tokens can expire or change!

```python
# User model (add field)
class User(Base):
    fcm_token = Column(String(500), nullable=True)

# Endpoint to update token
@router.post("/fcm-token")
async def update_fcm_token(
    fcm_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.fcm_token = fcm_token
    await db.commit()
    return {"success": True}
```

**Mobile app should update token:**
- On app startup
- After user login
- When token refreshes (Firebase SDK handles this)

### Handling Invalid Tokens

```python
try:
    messaging.send(message)
except messaging.UnregisteredError:
    # Token is invalid/expired
    # Remove from database
    user.fcm_token = None
    await db.commit()
except Exception as e:
    logger.error(f"Push failed: {e}")
```

### Push Notification Payload Structure

```python
message = messaging.Message(
    # Visual notification (shows on lock screen)
    notification=messaging.Notification(
        title='New Ride Request!',        # Bold headline
        body='Alice wants to join your ride'  # Description
    ),

    # Data payload (for app logic)
    data={
        'booking_id': '550e8400...',      # Open specific booking
        'type': 'booking_request',        # Determine action
        'screen': 'BookingDetails',       # Which screen to open
        'timestamp': '2026-01-05T12:00:00Z'
    },

    # Target
    token='user_fcm_token_here'
)
```

**Key Difference:**
- `notification` → System displays it (visible)
- `data` → Your app receives it (for logic/deep linking)

---

## 4. Email Templates with Jinja2

### Why Templates?

Hard-coding HTML in Python is messy:

```python
# ❌ Bad: Hard to maintain
html = f"<h1>Hi {name}</h1><p>Your ride to {destination} is confirmed!</p>"
```

Templates separate design from logic:

```html
<!-- ✅ Good: Clean and reusable -->
<h1>Hi {{ name }}</h1>
<p>Your ride to {{ destination }} is confirmed!</p>
```

### Jinja2 Basics

Jinja2 is a template engine that lets you inject variables into HTML.

**Variable Substitution:**
```html
<p>Hello {{ user_name }}!</p>
```

**Conditionals:**
```html
{% if is_driver %}
    <p>You have {{ passenger_count }} passengers</p>
{% else %}
    <p>Your driver is {{ driver_name }}</p>
{% endif %}
```

**Loops:**
```html
<ul>
{% for passenger in passengers %}
    <li>{{ passenger.name }} - {{ passenger.seats }} seats</li>
{% endfor %}
</ul>
```

**Template Inheritance:**
```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>
    <style>/* Common styles */</style>
</head>
<body>
    <div class="header">SJSU RideShare</div>
    {% block content %}{% endblock %}
    <div class="footer">© 2026</div>
</body>
</html>

<!-- booking_approved.html -->
{% extends "base.html" %}
{% block content %}
    <h2>Ride Approved!</h2>
    <p>Hi {{ passenger_name }}</p>
{% endblock %}
```

### Creating Email Templates

#### Example: Booking Approval Email

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: #28a745;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background: #f9f9f9;
            padding: 20px;
        }
        .ride-details {
            background: white;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }
        .button {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Great News!</h1>
        </div>

        <div class="content">
            <h2>Your Ride is Confirmed!</h2>

            <p>Hi {{ passenger_name }}!</p>
            <p><strong>{{ driver_name }}</strong> has approved your booking request.</p>

            <div class="ride-details">
                <h3>📍 Ride Details</h3>
                <p><strong>Driver:</strong> {{ driver_name }}</p>
                <p><strong>From:</strong> {{ origin }}</p>
                <p><strong>To:</strong> {{ destination }}</p>
                <p><strong>Departure:</strong> {{ departure_time }}</p>
                <p><strong>Seats:</strong> {{ seats_booked }}</p>
                <p><strong>Total:</strong> ${{ total_amount }}</p>
            </div>

            <p><strong>Important Reminders:</strong></p>
            <ul>
                <li>Be on time at the pickup location</li>
                <li>Bring exact change if paying cash</li>
                <li>Contact your driver if you need to cancel</li>
            </ul>

            <p style="text-align: center; margin: 30px 0;">
                <a href="{{ app_url }}/bookings/{{ booking_id }}" class="button">
                    View Booking Details
                </a>
            </p>
        </div>

        <div class="footer" style="background: #f5f5f5; padding: 15px; text-align: center;">
            <p>Have a safe trip! 🚗</p>
            <p>SJSU RideShare - Safe Carpooling for Students</p>
        </div>
    </div>
</body>
</html>
```

### Rendering Templates in Python

```python
from jinja2 import Template

def render_booking_approved(data: dict) -> str:
    """Render booking approval email"""
    with open('templates/email/booking_approved.html', 'r') as f:
        template = Template(f.read())

    return template.render(**data)

# Usage
html_content = render_booking_approved({
    'passenger_name': 'John Doe',
    'driver_name': 'Jane Smith',
    'origin': 'SJSU Campus',
    'destination': 'San Francisco Airport',
    'departure_time': 'Jan 10, 2026 at 9:00 AM',
    'seats_booked': 2,
    'total_amount': 25.00,
    'booking_id': '550e8400-e29b-41d4-a716-446655440000',
    'app_url': 'https://app.sjsurideshare.com'
})
```

### Email Design Best Practices

1. **Mobile-First Design**
   - 60% of emails opened on mobile
   - Use responsive width: `max-width: 600px`
   - Large, tappable buttons
   - Readable font size (16px+)

2. **Keep It Simple**
   - Single column layout
   - Clear hierarchy
   - Lots of whitespace
   - One primary action

3. **Accessibility**
   - Good color contrast
   - Alt text for images
   - Semantic HTML
   - Plain text fallback

4. **Email Client Compatibility**
   - Use inline CSS (not all clients support `<style>`)
   - Avoid complex CSS (flexbox, grid)
   - Test in Gmail, Outlook, iOS Mail

---

## 5. User Notification Preferences

### Why Preferences Matter

**User Control = Better Engagement**

Users should control:
- Which notifications they receive
- Which channels (email vs push)
- Frequency (immediate vs digest)

**Example: A commuter driver**
- ✅ Wants booking requests (both email + push)
- ✅ Wants ride reminders (email only)
- ❌ Doesn't want marketing emails
- ❌ Doesn't want push for payments

### Preference Data Model

```python
class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, unique=True, index=True)

    # Booking Requests (drivers receive)
    booking_requests_email = Column(Boolean, default=True)
    booking_requests_push = Column(Boolean, default=True)

    # Booking Updates (passengers receive)
    booking_updates_email = Column(Boolean, default=True)
    booking_updates_push = Column(Boolean, default=True)

    # Ride Reminders
    ride_reminders_email = Column(Boolean, default=True)
    ride_reminders_push = Column(Boolean, default=True)

    # Payments
    payment_email = Column(Boolean, default=True)
    payment_push = Column(Boolean, default=False)  # Less urgent

    # Marketing
    marketing_email = Column(Boolean, default=True)
    marketing_push = Column(Boolean, default=False)  # Opt-in
```

**Design Principles:**
1. Granular control (per type + channel)
2. Sensible defaults (most important things enabled)
3. Easy to change
4. Persistent (one row per user)

### Implementing Preference Logic

```python
class NotificationPreference(Base):
    # ... fields ...

    def get_channels_for_type(self, notification_type: str) -> list[str]:
        """
        Get enabled channels for a notification type.

        Args:
            notification_type: 'booking_request', 'booking_approved', etc.

        Returns:
            List of enabled channels: ['email', 'push'] or []
        """
        channels = []

        # Map notification type to preference fields
        type_mapping = {
            'booking_request': (
                self.booking_requests_email,
                self.booking_requests_push
            ),
            'booking_approved': (
                self.booking_updates_email,
                self.booking_updates_push
            ),
            'ride_reminder': (
                self.ride_reminders_email,
                self.ride_reminders_push
            ),
        }

        email_enabled, push_enabled = type_mapping.get(
            notification_type,
            (False, False)
        )

        if email_enabled:
            channels.append('email')
        if push_enabled:
            channels.append('push')

        return channels

# Usage
prefs = await get_user_preferences(user_id)
channels = prefs.get_channels_for_type('booking_request')

if 'email' in channels:
    await send_email(...)
if 'push' in channels:
    await send_push(...)
```

### Preference UI/UX Guidelines

**Mobile App Settings Screen:**
```
┌─────────────────────────────┐
│ Notification Settings       │
├─────────────────────────────┤
│                             │
│ Booking Requests            │
│ ☑ Email notifications       │
│ ☑ Push notifications        │
│                             │
│ Booking Updates             │
│ ☑ Email notifications       │
│ ☑ Push notifications        │
│                             │
│ Ride Reminders              │
│ ☑ Email notifications       │
│ ☐ Push notifications        │
│                             │
│ Payments                    │
│ ☑ Email receipts            │
│ ☐ Push notifications        │
│                             │
│ Marketing                   │
│ ☐ Promotional emails        │
│ ☐ Push announcements        │
│                             │
│      [Save Changes]         │
└─────────────────────────────┘
```

**Best Practices:**
1. Group by notification type
2. Clear labels
3. Default most important things ON
4. Explain what each does
5. Save immediately (no "Save" button needed)

---

## 6. Notification Delivery Architecture

### Overall Flow

```
┌──────────────┐
│ Event Occurs │ (e.g., booking approved)
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ Booking Service     │
│ - Updates database  │
│ - Calls Notif API   │
└─────────┬───────────┘
          │
          │ HTTP POST /api/v1/notifications/send/booking-approved
          ▼
┌──────────────────────────────────────────┐
│ Notification Service                     │
│                                          │
│ 1. Get user preferences                  │
│ 2. Determine channels (email/push/both)  │
│ 3. Create notification record            │
│ 4. Send via enabled channels             │
│ 5. Update delivery status                │
└──────────┬───────────────────────────────┘
           │
           ├─────────────┬─────────────┐
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Database │  │ SendGrid │  │ Firebase │
    │ (Record) │  │ (Email)  │  │  (Push)  │
    └──────────┘  └──────────┘  └──────────┘
```

### Service-to-Service Communication

**Option 1: Direct HTTP Calls (Current Implementation)**

```python
# booking-service calls notification-service
import httpx

async def notify_driver(driver_id, booking_data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://notification-service:8004/api/v1/notifications/send/booking-request",
            json={
                "driver_id": str(driver_id),
                "passenger_id": str(booking_data.passenger_id),
                "passenger_name": booking_data.passenger_name,
                # ... more data
            }
        )
    return response.status_code == 201
```

**Pros:**
- Simple and direct
- Immediate feedback
- Easy to debug

**Cons:**
- Synchronous (blocks until complete)
- No automatic retry
- If notification service is down, booking fails

**Option 2: Message Queue (Production-Ready)**

```python
# booking-service publishes to queue
await rabbitmq.publish(
    exchange='notifications',
    routing_key='booking.approved',
    message={
        'user_id': user_id,
        'type': 'booking_approved',
        'data': booking_data
    }
)

# notification-service consumes from queue
async def consume_notification_events():
    async for message in rabbitmq.consume('notifications'):
        await send_notification(message.data)
        message.ack()
```

**Pros:**
- Asynchronous (doesn't block)
- Automatic retry on failure
- Services are decoupled
- Can handle high volume

**Cons:**
- More complex setup
- Needs RabbitMQ/Redis infrastructure
- Eventual consistency

**When to Use:**
- Development/MVP: Direct HTTP (simpler)
- Production/Scale: Message Queue (more robust)

### Notification Record Lifecycle

```python
# 1. Create record
notification = Notification(
    user_id=user_id,
    type=NotificationType.BOOKING_APPROVED,
    channel=NotificationChannel.BOTH,
    title="Ride Approved!",
    message="Your ride has been confirmed",
    data={'booking_id': '123'},
    email_sent=False,
    push_sent=False,
    read=False
)
db.add(notification)
await db.commit()

# 2. Send email
email_sent = await send_email(...)
notification.email_sent = email_sent
notification.email_sent_at = datetime.utcnow()
await db.commit()

# 3. Send push
push_sent = await send_push(...)
notification.push_sent = push_sent
notification.push_sent_at = datetime.utcnow()
await db.commit()

# 4. User reads notification
notification.read = True
notification.read_at = datetime.utcnow()
await db.commit()
```

**Benefits of Storing Records:**
- Audit trail (when was notification sent?)
- Debugging (why didn't user get notification?)
- Analytics (open rates, delivery rates)
- In-app notification center (user can view history)

### Background Tasks vs Synchronous

```python
# ❌ Synchronous (blocks request)
@router.post("/bookings/{id}/approve")
async def approve_booking(booking_id):
    # Update database
    booking = await service.approve_booking(booking_id)

    # Send notification (BLOCKS for 2-3 seconds)
    await send_notification(booking)

    return booking  # User waits for notification to send

# ✅ Asynchronous (doesn't block)
from fastapi import BackgroundTasks

@router.post("/bookings/{id}/approve")
async def approve_booking(
    booking_id,
    background_tasks: BackgroundTasks
):
    # Update database
    booking = await service.approve_booking(booking_id)

    # Queue notification (returns immediately)
    background_tasks.add_task(send_notification, booking)

    return booking  # User gets response immediately
```

**Key Principle:** Never make users wait for non-critical operations.

---

## 7. Error Handling and Resilience

### The Golden Rule

**Notification failures should NEVER cause the main operation to fail.**

```python
# ❌ BAD: Booking fails if email fails
@router.post("/bookings")
async def create_booking(booking_data):
    booking = await create_booking(booking_data)
    await send_email(driver_email, ...)  # If this throws, booking fails!
    return booking

# ✅ GOOD: Booking succeeds even if email fails
@router.post("/bookings")
async def create_booking(booking_data):
    booking = await create_booking(booking_data)

    try:
        await send_email(driver_email, ...)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        # Continue anyway - booking is saved

    return booking
```

### Handling SendGrid Failures

```python
async def send_email(to_email, subject, html_content):
    """Send email with error handling"""
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid not configured - email not sent")
        return False

    try:
        response = sendgrid_client.send(message)

        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent to {to_email}")
            return True
        else:
            logger.error(
                f"SendGrid error: {response.status_code} - {response.body}"
            )
            return False

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False  # Don't crash!
```

**Common SendGrid Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Wrong API key | Check SENDGRID_API_KEY |
| 400 Bad Request | Invalid email format | Validate email before sending |
| 429 Too Many Requests | Rate limit exceeded | Implement rate limiting |
| Timeout | Network issue | Retry with backoff |

### Handling Firebase Failures

```python
async def send_push(fcm_token, title, body):
    """Send push notification with error handling"""
    if not firebase_enabled:
        logger.info("Firebase not configured - push not sent")
        return False

    try:
        response = messaging.send(message)
        logger.info(f"Push sent: {response}")
        return True

    except messaging.UnregisteredError:
        # Token is invalid/expired - remove it
        logger.warning(f"Invalid FCM token - removing from user")
        await remove_fcm_token(user_id)
        return False

    except messaging.SenderIdMismatchError:
        # Token belongs to different app
        logger.error("FCM token from wrong app")
        return False

    except Exception as e:
        logger.error(f"Push send failed: {e}")
        return False
```

**Common Firebase Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| UnregisteredError | Token expired/invalid | Remove token from database |
| SenderIdMismatchError | Token from different app | Validate app package name |
| QuotaExceededError | Too many messages | Implement rate limiting |
| Unavailable | Firebase service down | Retry later |

### Retry Logic with Exponential Backoff

```python
import asyncio
from typing import Callable

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
):
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds

    Returns:
        Result of function if successful, None otherwise
    """
    for attempt in range(max_retries):
        try:
            result = await func()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All retries failed: {e}")
                return None

            delay = base_delay * (2 ** attempt)  # Exponential: 1s, 2s, 4s
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
            await asyncio.sleep(delay)

# Usage
result = await retry_with_backoff(
    lambda: send_email(user_email, subject, content)
)
```

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    """
    Prevent cascading failures by stopping requests
    to a failing service after threshold is reached.
    """
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False

    async def call(self, func):
        # Circuit is open (too many failures)
        if self.is_open:
            # Check if timeout expired
            if time.time() - self.last_failure_time > self.timeout:
                self.is_open = False  # Try again
                self.failure_count = 0
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func()
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error("Circuit breaker opened")

            raise e

# Usage
sendgrid_breaker = CircuitBreaker()

async def send_email_safe(email, subject, content):
    try:
        return await sendgrid_breaker.call(
            lambda: send_email(email, subject, content)
        )
    except Exception:
        logger.info("Circuit breaker prevented email send")
        return False
```

---

## 8. Deep Linking and Mobile Integration

### What is Deep Linking?

Deep linking allows notifications to open specific screens in your mobile app.

**Example:**
```
User taps notification: "Ride Approved!"
    ↓
App opens directly to: Booking Details screen
    ↓
Shows booking #123 details
```

Without deep linking, app just opens to home screen (poor UX).

### Deep Link URL Schemes

```
# Custom URL scheme
sjsurideshare://booking/550e8400-e29b-41d4-a716-446655440000

# Universal link (HTTPS)
https://app.sjsurideshare.com/bookings/550e8400-e29b-41d4-a716-446655440000
```

**Universal links are better:**
- Work even if app not installed (opens web version)
- More secure
- Better for SEO

### Implementing Deep Links in Notifications

#### Email Deep Links

```html
<!-- In email template -->
<a href="https://app.sjsurideshare.com/bookings/{{ booking_id }}" class="button">
    View Booking Details
</a>

<!-- User clicks → Opens app → Navigates to booking screen -->
```

#### Push Notification Deep Links

```python
# Send push with data payload
message = messaging.Message(
    notification=messaging.Notification(
        title='Ride Approved!',
        body='Your ride to San Francisco is confirmed'
    ),
    data={
        'type': 'booking_approved',
        'booking_id': '550e8400-e29b-41d4-a716-446655440000',
        'screen': 'BookingDetails',
        'action': 'view'
    },
    token=user_fcm_token
)
```

**Mobile app handles data:**

```javascript
// React Native (JavaScript)
messaging().onNotificationOpenedApp(remoteMessage => {
    if (remoteMessage.data.screen === 'BookingDetails') {
        navigation.navigate('BookingDetails', {
            bookingId: remoteMessage.data.booking_id
        });
    }
});

// When app is in background/closed
messaging().getInitialNotification().then(remoteMessage => {
    if (remoteMessage) {
        // Handle deep link
    }
});
```

### Deep Link Best Practices

1. **Always include fallback**
   ```python
   data={
       'screen': 'BookingDetails',
       'booking_id': '123',
       'fallback_url': 'https://sjsurideshare.com/bookings/123'
   }
   ```

2. **Validate data on mobile side**
   ```javascript
   // Don't trust deep link data blindly
   const bookingId = remoteMessage.data.booking_id;
   if (isValidUUID(bookingId)) {
       navigation.navigate('BookingDetails', {bookingId});
   }
   ```

3. **Handle errors gracefully**
   ```javascript
   try {
       const booking = await fetchBooking(bookingId);
       showBookingDetails(booking);
   } catch (error) {
       // Booking not found or deleted
       showError("This booking is no longer available");
       navigation.navigate('Home');
   }
   ```

---

## 9. Best Practices for Notifications

### When to Send Notifications

**DO send for:**
- Time-sensitive information (ride in 1 hour)
- Actions requiring response (approve booking)
- Status changes user requested (booking approved)
- Important updates (ride cancelled)

**DON'T send for:**
- Low-priority updates (new blog post)
- Information user can discover themselves (new rides available)
- Too frequent updates (every new ride posted)
- Marketing without consent

### Notification Timing

```python
# ✅ GOOD: Immediate for urgent things
async def booking_approved():
    await send_notification_immediately()

# ✅ GOOD: Batched for non-urgent
async def daily_ride_digest():
    # Send once per day, not per ride
    rides = await get_new_rides_today()
    await send_digest_email(rides)

# ❌ BAD: Spamming
async def new_ride_posted():
    # Sends 50 notifications if 50 rides posted
    await send_notification()  # User unsubscribes!
```

### Writing Effective Notification Copy

**Be concise:**
```
❌ "Your booking request for a ride from San Jose State University to San Francisco International Airport has been approved by the driver Jane Smith"

✅ "Ride Approved! Jane approved your trip to SFO"
```

**Be actionable:**
```
❌ "You have a new notification"
✅ "Alice wants to join your ride - Approve or Reject"
```

**Use personalization:**
```
❌ "A passenger has requested to join a ride"
✅ "Alice wants to join your ride to San Francisco"
```

**Create urgency when appropriate:**
```
❌ "Your ride has been scheduled"
✅ "Your ride departs in 1 hour - Be ready!"
```

### Respecting User Privacy

1. **Don't include sensitive info in push notifications**
   ```python
   # ❌ BAD: Visible on lock screen
   title = "Payment of $25.00 processed"

   # ✅ GOOD: Vague but informative
   title = "Payment confirmed"
   # Details in app or email
   ```

2. **Provide easy opt-out**
   ```html
   <!-- In email footer -->
   <a href="{{ unsubscribe_url }}">Unsubscribe from these emails</a>
   ```

3. **Respect Do Not Disturb hours**
   ```python
   def should_send_push(user_tz, dnd_start=22, dnd_end=8):
       """Don't send push during night hours"""
       user_hour = datetime.now(user_tz).hour
       if dnd_start <= user_hour or user_hour < dnd_end:
           return False  # Send email instead
       return True
   ```

---

## 10. Testing Notification Systems

### Unit Tests

```python
@pytest.mark.asyncio
async def test_send_email_success(mock_sendgrid):
    """Test successful email sending"""
    mock_sendgrid.send.return_value = Mock(status_code=202)

    result = await email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>"
    )

    assert result is True
    mock_sendgrid.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure(mock_sendgrid):
    """Test email failure handling"""
    mock_sendgrid.send.side_effect = Exception("Network error")

    result = await email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>"
    )

    # Should not crash
    assert result is False


@pytest.mark.asyncio
async def test_respect_preferences(db_session):
    """Test notification preferences are respected"""
    user_id = uuid4()

    # Disable email for booking requests
    prefs = NotificationPreference(
        user_id=user_id,
        booking_requests_email=False,
        booking_requests_push=True
    )
    db_session.add(prefs)
    await db_session.commit()

    # Send notification
    service = NotificationService(db_session)
    notification = await service.send_notification(
        user_id=user_id,
        notification_type="booking_request",
        ...
    )

    # Email should NOT be sent
    assert notification.email_sent is False
    # Push should be sent
    assert notification.push_sent is True
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_notification():
    """Test complete notification flow"""
    # 1. Create booking
    booking = await create_booking(passenger_id, ride_id)

    # 2. Approve booking (triggers notification)
    await approve_booking(booking.id, driver_id)

    # 3. Verify notification was created
    notification = await get_latest_notification(passenger_id)
    assert notification.type == "booking_approved"
    assert notification.email_sent is True

    # 4. Verify email was queued
    emails = await get_sent_emails()  # Mock email server
    assert len(emails) == 1
    assert "Ride Approved" in emails[0].subject
```

### Manual Testing Checklist

**Email Testing:**
- [ ] Emails arrive in inbox (not spam)
- [ ] HTML renders correctly (Gmail, Outlook, iOS Mail)
- [ ] Links work and open correct pages
- [ ] Unsubscribe link works
- [ ] Responsive on mobile
- [ ] Plain text fallback works

**Push Testing:**
- [ ] Notifications appear on lock screen
- [ ] Tapping opens correct screen in app
- [ ] Sound/vibration works
- [ ] Badge count updates
- [ ] Works when app is closed
- [ ] Works when app is backgrounded
- [ ] Works on both Android and iOS

**Preference Testing:**
- [ ] Disabling email prevents email sending
- [ ] Disabling push prevents push sending
- [ ] Changes save correctly
- [ ] Default preferences are sensible

### Testing Tools

**SendGrid:**
```bash
# SendGrid Activity Feed
# View all sent emails in real-time
https://app.sendgrid.com/email_activity
```

**Firebase:**
```bash
# Firebase Console - Cloud Messaging
# View delivery stats and errors
https://console.firebase.google.com/project/YOUR_PROJECT/notification
```

**Email Testing Services:**
```bash
# Litmus - Test email rendering in 90+ clients
https://litmus.com

# Email on Acid - Email testing platform
https://www.emailonacid.com

# Mailtrap - Fake SMTP for development
https://mailtrap.io
```

---

## 11. Production Considerations

### Scaling Notifications

**Problem:** What if you need to send 10,000 notifications?

```python
# ❌ BAD: Sequential (takes forever)
for user in users:
    await send_notification(user)  # 10,000 × 2 seconds = 5.5 hours!

# ✅ GOOD: Batch processing
from asyncio import gather

async def send_batch(users):
    tasks = [send_notification(user) for user in users]
    await gather(*tasks)  # Parallel execution

# Send in batches of 100
for i in range(0, len(users), 100):
    batch = users[i:i+100]
    await send_batch(batch)
```

### Rate Limiting

**SendGrid free tier: 100 emails/day**

```python
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_per_day=100):
        self.max_per_day = max_per_day
        self.sent_today = 0
        self.last_reset = datetime.utcnow().date()

    async def can_send(self):
        # Reset counter if new day
        if datetime.utcnow().date() > self.last_reset:
            self.sent_today = 0
            self.last_reset = datetime.utcnow().date()

        return self.sent_today < self.max_per_day

    async def increment(self):
        self.sent_today += 1

# Usage
rate_limiter = RateLimiter(max_per_day=100)

async def send_email_with_rate_limit(email, subject, content):
    if not await rate_limiter.can_send():
        logger.warning("Rate limit exceeded - email queued")
        await queue_for_later(email, subject, content)
        return False

    result = await send_email(email, subject, content)
    if result:
        await rate_limiter.increment()
    return result
```

### Cost Optimization

**SendGrid Pricing:**
- Free: 100/day ($0)
- Essentials: 40,000/month ($15/month)
- Pro: 100,000/month ($90/month)

**Alternative: AWS SES**
- $0.10 per 1,000 emails
- 62,000 free/month (if hosted on EC2)

**When to switch:**
- Development: SendGrid free tier (easier setup)
- Production (< 3,000/month): SendGrid free tier
- Production (> 3,000/month): AWS SES (much cheaper)

**Migration to AWS SES:**

```python
import boto3

class EmailClient:
    def __init__(self):
        if settings.USE_AWS_SES:
            self.ses = boto3.client('ses', region_name='us-west-2')
        else:
            self.sendgrid = SendGridAPIClient(settings.SENDGRID_API_KEY)

    async def send_email(self, to_email, subject, html_content):
        if settings.USE_AWS_SES:
            return await self._send_via_ses(to_email, subject, html_content)
        else:
            return await self._send_via_sendgrid(to_email, subject, html_content)

    async def _send_via_ses(self, to_email, subject, html_content):
        try:
            response = self.ses.send_email(
                Source='noreply@sjsurideshare.com',
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': html_content}}
                }
            )
            return True
        except Exception as e:
            logger.error(f"SES error: {e}")
            return False
```

### Monitoring and Alerts

**Key Metrics to Track:**

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

emails_sent = Counter('emails_sent_total', 'Total emails sent')
emails_failed = Counter('emails_failed_total', 'Failed email sends')
email_send_duration = Histogram('email_send_seconds', 'Email send duration')

push_sent = Counter('push_sent_total', 'Total push notifications sent')
push_failed = Counter('push_failed_total', 'Failed push sends')

# Usage
with email_send_duration.time():
    result = await send_email(...)
    if result:
        emails_sent.inc()
    else:
        emails_failed.inc()
```

**Alerts to Set Up:**

1. **Email Failure Rate > 10%**
   ```
   Alert: Email delivery issues
   Check: SendGrid dashboard for bounce/spam reports
   ```

2. **Push Failure Rate > 20%**
   ```
   Alert: High push notification failures
   Check: Firebase console for token errors
   ```

3. **Rate Limit Reached**
   ```
   Alert: Daily email quota exceeded
   Action: Consider upgrading plan
   ```

---

## 12. Summary and Key Takeaways

### What You Learned

1. **Two Notification Channels**
   - Email (SendGrid) for permanent records
   - Push (Firebase) for instant alerts
   - User preferences for granular control

2. **Email Best Practices**
   - Use templates (Jinja2) for maintainability
   - Design mobile-first (60% open on mobile)
   - Keep out of spam (verified sender, good content)
   - Always provide unsubscribe

3. **Push Best Practices**
   - Include data payload for deep linking
   - Handle invalid tokens gracefully
   - Respect Do Not Disturb hours
   - Don't show sensitive info on lock screen

4. **Architecture Principles**
   - Separate notification service
   - Async/background processing
   - Graceful error handling
   - Never fail main operation if notification fails

5. **Testing & Monitoring**
   - Unit test with mocks
   - Integration test end-to-end
   - Monitor delivery rates
   - Alert on failures

### Common Pitfalls to Avoid

❌ **Blocking requests waiting for notifications**
- Use background tasks or message queues

❌ **Sending too many notifications**
- Batch non-urgent notifications
- Respect user preferences

❌ **Hard-coding email HTML in Python**
- Use templates for maintainability

❌ **Not handling failures gracefully**
- Log errors, don't crash
- Implement retry logic

❌ **Ignoring user privacy**
- Don't send sensitive info in push
- Provide easy opt-out

### Production Checklist

Before deploying to production:

- [ ] SendGrid sender email verified
- [ ] Firebase credentials secured (not in git)
- [ ] Rate limiting implemented
- [ ] Error monitoring set up (Sentry/DataDog)
- [ ] User preferences UI implemented
- [ ] Email templates tested in all clients
- [ ] Push notifications tested on iOS + Android
- [ ] Deep links working correctly
- [ ] Unsubscribe links working
- [ ] Database indexes on notification queries
- [ ] Circuit breakers for external services
- [ ] Metrics and alerts configured

### Next Steps

After completing Section 7:

1. **Test thoroughly**
   - Send test emails
   - Test push on real devices
   - Verify deep links work

2. **Optimize**
   - Monitor delivery rates
   - A/B test email subject lines
   - Track notification engagement

3. **Scale**
   - Implement message queue for high volume
   - Consider AWS SES for cost savings
   - Add notification digests (daily summaries)

4. **Enhance**
   - Add SMS notifications (Twilio)
   - Implement in-app notification center
   - Add notification sounds/vibrations customization

### Additional Resources

**Documentation:**
- [SendGrid Docs](https://docs.sendgrid.com)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [Jinja2 Templates](https://jinja.palletsprojects.com)

**Tools:**
- [Email Template Builder](https://beefree.io)
- [Email Testing](https://litmus.com)
- [Firebase Console](https://console.firebase.google.com)

**Best Practices:**
- [Email Deliverability Guide](https://sendgrid.com/blog/email-deliverability/)
- [Push Notification Guidelines](https://developer.apple.com/design/human-interface-guidelines/push-notifications)
- [GDPR Compliance for Emails](https://gdpr.eu/email-marketing/)

---

## Congratulations! 🎉

You've completed Section 7 and now understand:

✅ How to send emails with SendGrid
✅ How to send push notifications with Firebase
✅ How to create beautiful email templates
✅ How to manage user notification preferences
✅ How to build resilient notification systems
✅ How to test and monitor notifications

**Your RideShare app can now keep users informed in real-time!**

Move on to **Section 8: Real-Time Tracking** to add live location updates to rides.

---

**Questions or Issues?**

If you encounter problems implementing Section 7:
1. Check SendGrid Activity Feed for email issues
2. Check Firebase Console for push delivery stats
3. Review error logs for specific failures
4. Verify environment variables are set correctly

Happy coding! 🚀
