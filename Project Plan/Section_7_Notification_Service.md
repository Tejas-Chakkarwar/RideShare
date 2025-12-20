# SJSU RideShare Development Guide
## Section 7: Notification Service

**Version:** 1.0  
**Duration:** Week 7  
**Focus:** Email, Push Notifications, Templates, User Preferences

---

# SECTION 7: Notification Service

## Learning Objectives
- Build notification microservice
- Integrate SendGrid for email
- Integrate Firebase Cloud Messaging for push notifications
- Create email templates with Jinja2
- Manage notification preferences
- Handle notification failures gracefully

## Technologies
- FastAPI (new service)
- SendGrid (email - free 100/day)
- Firebase Cloud Messaging (push - free unlimited)
- Jinja2 (email templates)
- Redis (for queuing - optional)

## Prerequisites
- Sections 1-6 completed ✅
- SendGrid account (free tier)
- Firebase project
- Understanding of email/push notifications

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Notification Service

CONTEXT:
Sections 1-6 completed. Bookings working.
Creating notification-service for sending emails and push notifications.
Section 7 of 13.

GOAL:
Build notification service that sends:
- Email notifications via SendGrid
- Push notifications via Firebase
- Supports templates and user preferences
- Handles failures gracefully

DETAILED REQUIREMENTS:

1. CREATE NOTIFICATION-SERVICE STRUCTURE:

   backend/services/notification-service/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── api/routes/
   │   │   ├── health.py
   │   │   └── notifications.py
   │   ├── core/
   │   │   ├── config.py
   │   │   ├── database.py
   │   ├── models/
   │   │   ├── notification.py
   │   │   └── notification_preference.py
   │   ├── schemas/
   │   │   └── notification.py
   │   ├── services/
   │   │   ├── email_service.py
   │   │   ├── push_service.py
   │   │   └── notification_service.py
   │   ├── templates/
   │   │   └── email/
   │   │       ├── base.html
   │   │       ├── booking_request.html
   │   │       ├── booking_approved.html
   │   │       ├── booking_rejected.html
   │   │       ├── booking_cancelled.html
   │   │       ├── ride_reminder.html
   │   │       └── review_request.html
   │   └── utils/
   │       └── template_renderer.py
   ├── tests/
   ├── Dockerfile
   └── requirements.txt

2. NOTIFICATION MODEL (app/models/notification.py):

   Fields:
   - id: UUID
   - user_id: UUID (recipient)
   - type: Enum ("booking_request", "booking_approved", "booking_rejected", 
                 "booking_cancelled", "ride_reminder", "payment_confirmation",
                 "review_request", "system_announcement")
   - channel: Enum ("email", "push", "both")
   - title: String(200)
   - message: Text
   - data: JSON (additional data for deep linking)
   - email_sent: Boolean (default False)
   - email_sent_at: DateTime (nullable)
   - push_sent: Boolean (default False)
   - push_sent_at: DateTime (nullable)
   - read: Boolean (default False)
   - read_at: DateTime (nullable)
   - created_at: DateTime
   
   Indexes:
   - (user_id, created_at)
   - type
   - read

3. NOTIFICATION PREFERENCE MODEL (app/models/notification_preference.py):

   Fields:
   - id: UUID
   - user_id: UUID (unique)
   - booking_requests_email: Boolean (default True)
   - booking_requests_push: Boolean (default True)
   - booking_updates_email: Boolean (default True)
   - booking_updates_push: Boolean (default True)
   - ride_reminders_email: Boolean (default True)
   - ride_reminders_push: Boolean (default True)
   - payment_email: Boolean (default True)
   - payment_push: Boolean (default False)
   - marketing_email: Boolean (default True)
   - marketing_push: Boolean (default False)
   - created_at, updated_at: DateTime

4. SENDGRID SETUP (app/services/email_service.py):

   Setup:
   - Sign up at sendgrid.com (free tier: 100 emails/day)
   - Create API key
   - Verify sender email
   - Add to .env: SENDGRID_API_KEY
   
   Implementation:
   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail
   
   class EmailService:
       def __init__(self):
           self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
           self.from_email = "noreply@sjsurideshare.com"
       
       async def send_email(
           self,
           to_email: str,
           subject: str,
           html_content: str,
           text_content: str = None
       ) -> bool:
           """Send email via SendGrid"""
           try:
               message = Mail(
                   from_email=self.from_email,
                   to_emails=to_email,
                   subject=subject,
                   html_content=html_content,
                   plain_text_content=text_content
               )
               
               response = self.sg.send(message)
               
               if response.status_code in [200, 201, 202]:
                   logger.info(f"Email sent to {to_email}")
                   return True
               else:
                   logger.error(f"Email failed: {response.status_code}")
                   return False
           
           except Exception as e:
               logger.error(f"SendGrid error: {e}")
               return False
       
       async def send_templated_email(
           self,
           to_email: str,
           template_name: str,
           context: dict
       ) -> bool:
           """Send email using Jinja2 template"""
           # Render template
           html = render_template(template_name, context)
           subject = context.get('subject', 'SJSU RideShare Notification')
           
           return await self.send_email(to_email, subject, html)
   ```

5. FIREBASE PUSH SETUP (app/services/push_service.py):

   Setup:
   - Go to console.firebase.google.com
   - Create project
   - Add Android/iOS app
   - Download firebase-credentials.json
   - Add to .env: FIREBASE_CREDENTIALS_PATH
   
   Implementation:
   ```python
   import firebase_admin
   from firebase_admin import credentials, messaging
   
   class PushService:
       def __init__(self):
           cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
           firebase_admin.initialize_app(cred)
       
       async def send_push(
           self,
           fcm_token: str,
           title: str,
           body: str,
           data: dict = None
       ) -> bool:
           """Send push notification via Firebase"""
           try:
               message = messaging.Message(
                   notification=messaging.Notification(
                       title=title,
                       body=body
                   ),
                   data=data or {},
                   token=fcm_token
               )
               
               response = messaging.send(message)
               logger.info(f"Push sent: {response}")
               return True
           
           except messaging.UnregisteredError:
               logger.warning(f"Invalid token: {fcm_token}")
               return False
           except Exception as e:
               logger.error(f"Push failed: {e}")
               return False
       
       async def send_push_to_user(
           self,
           user_id: UUID,
           title: str,
           body: str,
           data: dict = None
       ) -> bool:
           """Send push to user (get FCM token from user-service)"""
           # Call user-service to get FCM token
           user = await user_client.get_user(user_id)
           if not user or not user.get('fcm_token'):
               logger.warning(f"No FCM token for user {user_id}")
               return False
           
           return await self.send_push(user['fcm_token'], title, body, data)
   ```

6. EMAIL TEMPLATES (Jinja2):

   Base Template (templates/email/base.html):
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <style>
           body { font-family: Arial, sans-serif; }
           .container { max-width: 600px; margin: 0 auto; }
           .header { background: #0066cc; color: white; padding: 20px; }
           .content { padding: 20px; }
           .button { background: #0066cc; color: white; padding: 10px 20px; 
                     text-decoration: none; border-radius: 5px; }
           .footer { background: #f5f5f5; padding: 20px; text-align: center; }
       </style>
   </head>
   <body>
       <div class="container">
           <div class="header">
               <h1>SJSU RideShare</h1>
           </div>
           <div class="content">
               {% block content %}{% endblock %}
           </div>
           <div class="footer">
               <p>SJSU RideShare - Safe Carpooling for Students</p>
               <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
           </div>
       </div>
   </body>
   </html>
   ```
   
   Booking Request Template (templates/email/booking_request.html):
   ```html
   {% extends "base.html" %}
   {% block content %}
   <h2>New Ride Request!</h2>
   <p>{{passenger_name}} wants to join your ride.</p>
   
   <div style="background: #f9f9f9; padding: 15px; margin: 20px 0;">
       <p><strong>Route:</strong> {{origin}} → {{destination}}</p>
       <p><strong>Date:</strong> {{departure_time}}</p>
       <p><strong>Seats:</strong> {{seats_booked}}</p>
       <p><strong>Amount:</strong> ${{amount}}</p>
   </div>
   
   <div style="background: #e8f4fd; padding: 15px; margin: 20px 0;">
       <p><strong>Passenger Rating:</strong> {{passenger_rating}} ⭐</p>
       <p><strong>Message:</strong> {{passenger_notes}}</p>
   </div>
   
   <p>
       <a href="{{approve_url}}" class="button">Approve</a>
       <a href="{{reject_url}}" class="button" style="background: #dc3545;">Reject</a>
   </p>
   {% endblock %}
   ```
   
   Create similar templates for:
   - booking_approved.html
   - booking_rejected.html
   - booking_cancelled.html
   - ride_reminder.html
   - review_request.html

7. NOTIFICATION SERVICE (app/services/notification_service.py):

   Key Functions:
   
   ```python
   async def send_notification(
       user_id: UUID,
       notification_type: str,
       data: dict,
       db: AsyncSession
   ) -> Notification:
       """
       Main function to send notification
       - Checks user preferences
       - Creates notification record
       - Sends via appropriate channels
       """
       # Get user preferences
       prefs = await get_user_preferences(user_id, db)
       
       # Determine channels
       channels = determine_channels(notification_type, prefs)
       
       # Create notification record
       notification = Notification(
           user_id=user_id,
           type=notification_type,
           channel=channels,
           title=data.get('title'),
           message=data.get('message'),
           data=data
       )
       db.add(notification)
       await db.commit()
       
       # Send via channels
       if 'email' in channels:
           email_sent = await email_service.send_templated_email(
               user_email,
               template_name,
               data
           )
           notification.email_sent = email_sent
           if email_sent:
               notification.email_sent_at = datetime.utcnow()
       
       if 'push' in channels:
           push_sent = await push_service.send_push_to_user(
               user_id,
               data.get('title'),
               data.get('message'),
               data.get('data')
           )
           notification.push_sent = push_sent
           if push_sent:
               notification.push_sent_at = datetime.utcnow()
       
       await db.commit()
       return notification
   ```
   
   Specific Notification Functions:
   
   A. send_booking_request_notification(driver_id, booking_data):
   ```python
   data = {
       'title': 'New Ride Request!',
       'message': f"{passenger_name} wants to join your ride",
       'passenger_name': booking_data['passenger_name'],
       'passenger_rating': booking_data['passenger_rating'],
       'origin': booking_data['origin_address'],
       'destination': booking_data['destination_address'],
       'seats_booked': booking_data['seats_booked'],
       'amount': booking_data['amount'],
       'passenger_notes': booking_data['passenger_notes'],
       'approve_url': f"https://app.sjsurideshare.com/bookings/{booking_id}/approve",
       'reject_url': f"https://app.sjsurideshare.com/bookings/{booking_id}/reject"
   }
   await send_notification(driver_id, 'booking_request', data, db)
   ```
   
   B. send_booking_approved_notification(passenger_id, booking_data):
   C. send_booking_rejected_notification(passenger_id, booking_data):
   D. send_booking_cancelled_notification(user_id, booking_data):
   E. send_ride_reminder_notification(user_id, booking_data):
   F. send_review_request_notification(user_id, booking_data):

8. USER PREFERENCES:

   Default preferences (all notifications enabled):
   ```python
   async def create_default_preferences(user_id: UUID, db: AsyncSession):
       prefs = NotificationPreference(
           user_id=user_id,
           booking_requests_email=True,
           booking_requests_push=True,
           booking_updates_email=True,
           booking_updates_push=True,
           ride_reminders_email=True,
           ride_reminders_push=True,
           payment_email=True,
           payment_push=False,  # Don't spam with payment push
           marketing_email=True,
           marketing_push=False
       )
       db.add(prefs)
       await db.commit()
   ```

9. FCM TOKEN MANAGEMENT:

   Update user-service User model:
   - Add field: fcm_token: String(500) (nullable)
   
   Add endpoint to user-service:
   ```python
   POST /api/v1/users/fcm-token
   {
       "fcm_token": "device_token_here"
   }
   ```
   
   Mobile app calls this on:
   - Login
   - App startup
   - Token refresh

10. API ROUTES (app/api/routes/notifications.py):

    POST /api/v1/notifications/send (internal only):
    - Called by other services
    - Send notification
    - Returns 201
    
    GET /api/v1/notifications/me (protected):
    - Get user's notifications
    - Query: read=true/false (filter)
    - Returns paginated list
    
    PUT /api/v1/notifications/{id}/read (protected):
    - Mark as read
    - Returns 200
    
    GET /api/v1/notifications/preferences (protected):
    - Get preferences
    - Returns NotificationPreferenceResponse
    
    PUT /api/v1/notifications/preferences (protected):
    - Update preferences
    - Returns 200
    
    DELETE /api/v1/notifications/{id} (protected):
    - Delete notification
    - Returns 204

11. SCHEDULED NOTIFICATIONS:

    Create background job (optional - can use cron):
    ```python
    # Run daily at 9 AM
    async def send_ride_reminders():
        """Send reminders for rides departing in 24 hours"""
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start = tomorrow.replace(hour=0, minute=0)
        end = tomorrow.replace(hour=23, minute=59)
        
        # Get all bookings with rides departing tomorrow
        bookings = await get_bookings_in_timeframe(start, end, db)
        
        for booking in bookings:
            # Send to passenger
            await send_ride_reminder_notification(
                booking.passenger_id,
                booking,
                db
            )
            
            # Send to driver (if not already sent)
            # ...
    ```

12. DOCKER CONFIGURATION:

    ```yaml
    notification-service:
      build: ./services/notification-service
      ports: ["8004:8000"]
      environment:
        - DATABASE_URL=...
        - SENDGRID_API_KEY=${SENDGRID_API_KEY}
        - FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
        - USER_SERVICE_URL=http://user-service:8000
      volumes:
        - ./firebase-credentials.json:/app/firebase-credentials.json:ro
      depends_on: [postgres, redis, user-service]
    ```

13. REQUIREMENTS.txt:

    Add:
    ```
    sendgrid==6.11.0
    firebase-admin==6.2.0
    jinja2==3.1.2
    ```

14. ERROR HANDLING:

    Handle failures gracefully:
    - SendGrid rate limit: Queue for later
    - Invalid email: Log and skip
    - Invalid FCM token: Update user record
    - Service timeout: Retry with backoff
    
    Don't fail the main operation if notification fails!

15. GENERATE LEARNING DOCUMENTATION:

    Create: docs/learning/07-notifications-and-messaging.md
    
    Cover (15 pages):
    1. Email vs Push Notifications
    2. SendGrid Integration
    3. Firebase Cloud Messaging
    4. Email Templates with Jinja2
    5. User Preferences Management
    6. Notification Best Practices
    7. Deliverability and Spam
    8. Deep Linking in Notifications
    9. Error Handling
    10. Testing Notifications

16. TESTING (tests/test_notifications.py):

    Mock SendGrid and Firebase:
    - test_send_email
    - test_send_push
    - test_respect_preferences (if disabled, don't send)
    - test_create_notification_record
    - test_mark_as_read
    - test_update_preferences
    - test_email_template_rendering
    - test_invalid_fcm_token
    - test_sendgrid_failure

17. POSTMAN COLLECTION:

    Add "Notifications" folder:
    - Send Notification (internal)
    - Get My Notifications
    - Mark Notification as Read
    - Get Preferences
    - Update Preferences
    - Delete Notification

VERIFICATION CHECKLIST:
- [ ] Service runs on port 8004
- [ ] SendGrid account setup
- [ ] Can send test email
- [ ] Firebase project setup
- [ ] Can send test push
- [ ] Templates render correctly
- [ ] Preferences respected
- [ ] Email disabled → no email sent
- [ ] Push disabled → no push sent
- [ ] FCM token endpoint works
- [ ] Notification record created
- [ ] Mark as read works
- [ ] All templates exist
- [ ] Deep links work (in mobile app)
- [ ] Error handling works
- [ ] All tests pass

Please generate notification service with SendGrid and Firebase integration.
```

---

## TESTING CHECKLIST - SECTION 7

### Setup
- [ ] Notification-service created
- [ ] SendGrid account created (free tier)
- [ ] SendGrid API key generated
- [ ] Sender email verified in SendGrid
- [ ] Firebase project created
- [ ] Firebase credentials downloaded
- [ ] Port 8004 configured

### SendGrid Integration
- [ ] API key in .env
- [ ] Send test email via API
- [ ] Email received
- [ ] HTML renders correctly
- [ ] Links work

### Firebase Integration
- [ ] Credentials file present
- [ ] Firebase initialized
- [ ] Can send test push
- [ ] Push received on device

### Email Templates
- [ ] Base template exists
- [ ] All specific templates created:
  - [ ] booking_request.html
  - [ ] booking_approved.html
  - [ ] booking_rejected.html
  - [ ] booking_cancelled.html
  - [ ] ride_reminder.html
  - [ ] review_request.html
- [ ] Templates render with test data
- [ ] Variables replaced correctly
- [ ] CSS styles applied

### Notification Types

#### Booking Request
Trigger: Passenger creates booking
- [ ] Email sent to driver
- [ ] Push sent to driver
- [ ] Contains passenger info
- [ ] Contains approve/reject links
- [ ] Notification record created

#### Booking Approved
Trigger: Driver approves booking
- [ ] Email sent to passenger
- [ ] Push sent to passenger
- [ ] Contains ride details
- [ ] Contains driver info

#### Booking Rejected
Trigger: Driver rejects booking
- [ ] Email sent to passenger
- [ ] Contains rejection reason
- [ ] Polite and helpful message

#### Booking Cancelled
Trigger: Passenger or driver cancels
- [ ] Email to other party
- [ ] Explains who cancelled
- [ ] Refund information included

### User Preferences
- [ ] Default preferences created on signup
- [ ] Can get preferences
- [ ] Can update preferences
- [ ] Disable email: no email sent
- [ ] Disable push: no push sent
- [ ] Both disabled: no notifications

### Notification Records
- [ ] Record created in database
- [ ] email_sent flag updated
- [ ] push_sent flag updated
- [ ] Timestamps recorded
- [ ] Can get user's notifications
- [ ] Can mark as read
- [ ] read_at timestamp updated

### FCM Token Management
- [ ] User model updated with fcm_token field
- [ ] Endpoint to update token works
- [ ] Token stored correctly
- [ ] Push uses correct token
- [ ] Invalid token handled

### Error Handling
- [ ] SendGrid failure: logged, not crashed
- [ ] Firebase failure: logged, not crashed
- [ ] Invalid email: handled
- [ ] Invalid FCM token: handled
- [ ] Template rendering error: handled
- [ ] User service down: handled

### Integration
- [ ] Other services can call notification service
- [ ] Booking service triggers notifications
- [ ] Notifications sent asynchronously
- [ ] Main operation not blocked by notification failure

### Performance
- [ ] Notification sent < 1 second
- [ ] Doesn't block main request
- [ ] Template rendering fast

### Learning
- [ ] Read 07-notifications-and-messaging.md
- [ ] Understand email vs push
- [ ] Understand SendGrid
- [ ] Understand Firebase
- [ ] Understand templates

### Completion
- [ ] All tests passing
- [ ] Can send emails
- [ ] Can send push notifications
- [ ] Templates working
- [ ] Preferences working
- [ ] Ready for Section 8

---

**Date Completed:** _______________  
**SendGrid Emails Sent:** _____  
**Firebase Pushes Sent:** _____  
**Notes:** _______________
