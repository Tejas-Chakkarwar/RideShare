# Migration: Add FCM Token to User Model

**Purpose:** Add support for Firebase Cloud Messaging (push notifications) to user model.

**Section:** 7 - Notification Service

**Date:** January 5, 2026

---

## What Changed

Added `fcm_token` field to User model to store Firebase Cloud Messaging tokens for push notifications.

---

## Manual Database Migration

If not using Alembic, run this SQL:

```sql
-- Add fcm_token column to users table
ALTER TABLE users
ADD COLUMN fcm_token VARCHAR(500) NULL;

-- Add comment
COMMENT ON COLUMN users.fcm_token IS 'Firebase Cloud Messaging token for push notifications';
```

---

## Alembic Migration (Recommended)

### Step 1: Create Migration

```bash
cd backend/services/user-service

# Generate migration
alembic revision -m "Add FCM token field to users"
```

This creates a new file in `alembic/versions/`.

### Step 2: Edit Migration File

Open the generated file and add:

```python
"""Add FCM token field to users

Revision ID: xxxxxxxxxxxx
Revises: previous_revision
Create Date: 2026-01-05 12:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'xxxxxxxxxxxx'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    """Add fcm_token column for push notifications"""
    op.add_column(
        'users',
        sa.Column('fcm_token', sa.String(500), nullable=True)
    )


def downgrade():
    """Remove fcm_token column"""
    op.drop_column('users', 'fcm_token')
```

### Step 3: Run Migration

```bash
# Apply migration
alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Running upgrade previous -> xxxx, Add FCM token field to users
```

### Step 4: Verify

```bash
# Connect to database
psql -U postgres -d rideshare_users

# Check column exists
\d users

# You should see:
# fcm_token | character varying(500) |
```

---

## Verify Code Changes

The following files were already updated:

### 1. User Model

**File:** `app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...

    # Push Notifications (Section 7)
    fcm_token = Column(String(500), nullable=True)

    # ... rest of model ...
```

### 2. User API Routes

**File:** `app/api/routes/users.py`

```python
@router.post("/fcm-token", status_code=status.HTTP_200_OK)
async def update_fcm_token(
    fcm_token: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update FCM token for push notifications"""
    current_user.fcm_token = fcm_token
    db.add(current_user)
    await db.commit()
    return {"success": True, "message": "FCM token updated successfully"}
```

---

## Testing the Changes

### 1. Test Migration

```bash
# Rollback
alembic downgrade -1

# Should remove fcm_token column

# Re-apply
alembic upgrade head

# Should add fcm_token column back
```

### 2. Test API Endpoint

```bash
# Start user service
uvicorn app.main:app --reload --port 8001

# Update FCM token (requires authentication)
curl -X POST http://localhost:8001/api/v1/users/fcm-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"fcm_token": "test_token_here"}'

# Response:
# {"success": true, "message": "FCM token updated successfully"}
```

### 3. Verify in Database

```sql
-- Check user's FCM token
SELECT id, email, fcm_token FROM users WHERE email = 'test@example.com';
```

---

## Mobile App Integration

### React Native Example

```javascript
import messaging from '@react-native-firebase/messaging';
import axios from 'axios';

// Request permission (iOS)
async function requestPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Authorization status:', authStatus);
  }
}

// Get FCM token
async function getFCMToken() {
  const token = await messaging().getToken();
  return token;
}

// Send token to backend
async function updateFCMToken() {
  try {
    const token = await getFCMToken();

    await axios.post(
      'https://api.sjsurideshare.com/api/v1/users/fcm-token',
      { fcm_token: token },
      {
        headers: {
          'Authorization': `Bearer ${userAuthToken}`
        }
      }
    );

    console.log('FCM token updated successfully');
  } catch (error) {
    console.error('Failed to update FCM token:', error);
  }
}

// Call on app startup and login
export async function initializePushNotifications() {
  await requestPermission();
  await updateFCMToken();

  // Update token when it refreshes
  messaging().onTokenRefresh(async (token) => {
    await updateFCMToken();
  });
}
```

### Flutter Example

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> initializePushNotifications() async {
  // Request permission (iOS)
  NotificationSettings settings = await FirebaseMessaging.instance.requestPermission();

  if (settings.authorizationStatus == AuthorizationStatus.authorized) {
    // Get FCM token
    String? token = await FirebaseMessaging.instance.getToken();

    if (token != null) {
      await updateFCMToken(token);
    }

    // Listen for token refresh
    FirebaseMessaging.instance.onTokenRefresh.listen(updateFCMToken);
  }
}

Future<void> updateFCMToken(String token) async {
  try {
    final response = await http.post(
      Uri.parse('https://api.sjsurideshare.com/api/v1/users/fcm-token'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $userAuthToken',
      },
      body: jsonEncode({'fcm_token': token}),
    );

    if (response.statusCode == 200) {
      print('FCM token updated successfully');
    }
  } catch (e) {
    print('Failed to update FCM token: $e');
  }
}
```

---

## Rollback Instructions

If you need to rollback:

```bash
# Using Alembic
alembic downgrade -1

# Or manually
psql -U postgres -d rideshare_users -c "ALTER TABLE users DROP COLUMN fcm_token;"
```

---

## Security Considerations

1. **Token Storage**
   - FCM tokens are not sensitive (safe to store in database)
   - They can't be used to access user data
   - They're device-specific, not user-specific

2. **Token Lifecycle**
   - Tokens can expire (Firebase handles this)
   - Mobile app should update on token refresh
   - Invalid tokens should be handled gracefully

3. **Privacy**
   - Push notifications can be seen on lock screen
   - Don't include sensitive info in notification body
   - Use data payload for sensitive information

---

## Troubleshooting

### Issue: Migration fails with "column already exists"

```sql
-- Check if column exists
SELECT column_name FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'fcm_token';

-- If it exists, mark migration as applied
alembic stamp head
```

### Issue: Can't update FCM token (401 Unauthorized)

- Verify JWT token is valid
- Check authentication middleware is working
- Ensure user is logged in

### Issue: FCM token not saving

```python
# Check if commit is being called
current_user.fcm_token = fcm_token
db.add(current_user)  # Important!
await db.commit()      # Important!
```

---

## Verification Checklist

After migration, verify:

- [ ] Column exists in database
- [ ] Column is nullable (NULL allowed)
- [ ] Column type is VARCHAR(500)
- [ ] API endpoint `/fcm-token` is accessible
- [ ] Can update FCM token via API
- [ ] Token persists after update
- [ ] No breaking changes to existing code

---

## Next Steps

1. **Deploy Migration**
   ```bash
   # On production server
   alembic upgrade head
   ```

2. **Update Mobile App**
   - Add Firebase SDK
   - Request notification permission
   - Get and send FCM token to backend

3. **Test Push Notifications**
   - Use notification service to send test push
   - Verify delivery on device

4. **Monitor**
   - Track invalid token errors
   - Monitor token refresh rate
   - Check notification delivery rates

---

## Related Documentation

- Notification Service: `backend/services/notification-service/README.md`
- Learning Guide: `docs/learning/07-notifications-and-messaging.md`
- Section 7 Summary: `docs/SECTION_7_COMPLETION_SUMMARY.md`

---

**Migration Status:** ✅ Code Updated, Database Migration Pending

**Last Updated:** January 5, 2026
