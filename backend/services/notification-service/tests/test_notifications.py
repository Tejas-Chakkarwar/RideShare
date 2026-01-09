"""
Tests for Notification Service

Tests cover:
- Email sending (mocked SendGrid)
- Push notifications (mocked Firebase)
- Notification preferences
- Notification records
- API endpoints
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.models.notification_preference import NotificationPreference
from app.services.notification_service import NotificationService


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def user_id():
    """Test user ID"""
    return uuid4()


@pytest.fixture
def mock_email_service():
    """Mock email service"""
    with patch('app.services.notification_service.email_service') as mock:
        mock.send_email = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_push_service():
    """Mock push service"""
    with patch('app.services.notification_service.push_service') as mock:
        mock.send_push_to_user = AsyncMock(return_value=True)
        yield mock


@pytest.mark.asyncio
async def test_create_default_preferences(db_session, user_id):
    """Test creating default notification preferences"""
    service = NotificationService(db_session)

    prefs = await service.get_or_create_preferences(user_id)

    assert prefs.user_id == user_id
    assert prefs.booking_requests_email is True
    assert prefs.booking_requests_push is True
    assert prefs.booking_updates_email is True
    assert prefs.booking_updates_push is True
    assert prefs.ride_reminders_email is True
    assert prefs.ride_reminders_push is True
    assert prefs.payment_email is True
    assert prefs.payment_push is False  # Default off for payments
    assert prefs.marketing_email is True
    assert prefs.marketing_push is False  # Default off for marketing


@pytest.mark.asyncio
async def test_get_existing_preferences(db_session, user_id):
    """Test retrieving existing preferences"""
    # Create preferences
    prefs = NotificationPreference(
        user_id=user_id,
        booking_requests_email=False
    )
    db_session.add(prefs)
    await db_session.commit()

    # Retrieve
    service = NotificationService(db_session)
    retrieved = await service.get_or_create_preferences(user_id)

    assert retrieved.user_id == user_id
    assert retrieved.booking_requests_email is False


@pytest.mark.asyncio
async def test_update_preferences(db_session, user_id):
    """Test updating notification preferences"""
    service = NotificationService(db_session)

    # Create default
    await service.get_or_create_preferences(user_id)

    # Update
    updates = {
        'booking_requests_email': False,
        'booking_requests_push': False,
        'marketing_email': False
    }
    updated = await service.update_preferences(user_id, updates)

    assert updated.booking_requests_email is False
    assert updated.booking_requests_push is False
    assert updated.marketing_email is False
    assert updated.booking_updates_email is True  # Unchanged


@pytest.mark.asyncio
async def test_send_notification_both_channels(
    db_session,
    user_id,
    mock_email_service,
    mock_push_service
):
    """Test sending notification via both email and push"""
    service = NotificationService(db_session)

    # Create preferences (all enabled by default)
    await service.get_or_create_preferences(user_id)

    # Send notification
    notification = await service.send_notification(
        user_id=user_id,
        user_email="test@example.com",
        fcm_token="test_token",
        notification_type=NotificationType.BOOKING_REQUEST,
        title="New Ride Request",
        message="Passenger wants to join your ride",
        email_content="<html>Email content</html>"
    )

    # Verify notification created
    assert notification.user_id == user_id
    assert notification.type == NotificationType.BOOKING_REQUEST
    assert notification.title == "New Ride Request"

    # Verify both channels attempted
    assert notification.email_sent is True
    assert notification.push_sent is True
    assert notification.email_sent_at is not None
    assert notification.push_sent_at is not None


@pytest.mark.asyncio
async def test_respect_email_disabled_preference(
    db_session,
    user_id,
    mock_email_service,
    mock_push_service
):
    """Test that email is not sent when preference is disabled"""
    service = NotificationService(db_session)

    # Create preferences with email disabled
    await service.get_or_create_preferences(user_id)
    await service.update_preferences(user_id, {'booking_requests_email': False})

    # Send notification
    notification = await service.send_notification(
        user_id=user_id,
        user_email="test@example.com",
        fcm_token="test_token",
        notification_type=NotificationType.BOOKING_REQUEST,
        title="New Ride Request",
        message="Test message",
        email_content="<html>Email content</html>"
    )

    # Verify email NOT sent but push IS sent
    assert notification.email_sent is False
    assert notification.push_sent is True


@pytest.mark.asyncio
async def test_respect_push_disabled_preference(
    db_session,
    user_id,
    mock_email_service,
    mock_push_service
):
    """Test that push is not sent when preference is disabled"""
    service = NotificationService(db_session)

    # Create preferences with push disabled
    await service.get_or_create_preferences(user_id)
    await service.update_preferences(user_id, {'booking_requests_push': False})

    # Send notification
    notification = await service.send_notification(
        user_id=user_id,
        user_email="test@example.com",
        fcm_token="test_token",
        notification_type=NotificationType.BOOKING_REQUEST,
        title="New Ride Request",
        message="Test message",
        email_content="<html>Email content</html>"
    )

    # Verify push NOT sent but email IS sent
    assert notification.email_sent is True
    assert notification.push_sent is False


@pytest.mark.asyncio
async def test_get_user_notifications(db_session, user_id):
    """Test retrieving user notifications"""
    # Create some notifications
    notif1 = Notification(
        user_id=user_id,
        type=NotificationType.BOOKING_REQUEST,
        channel=NotificationChannel.BOTH,
        title="Notification 1",
        message="Message 1",
        read=False
    )
    notif2 = Notification(
        user_id=user_id,
        type=NotificationType.BOOKING_APPROVED,
        channel=NotificationChannel.EMAIL,
        title="Notification 2",
        message="Message 2",
        read=True
    )
    db_session.add_all([notif1, notif2])
    await db_session.commit()

    service = NotificationService(db_session)

    # Get all notifications
    notifications, total, unread_count = await service.get_user_notifications(user_id)

    assert total == 2
    assert unread_count == 1
    assert len(notifications) == 2

    # Get only unread
    notifications, total, unread_count = await service.get_user_notifications(
        user_id,
        unread_only=True
    )

    assert len(notifications) == 1
    assert notifications[0].title == "Notification 1"


@pytest.mark.asyncio
async def test_mark_as_read(db_session, user_id):
    """Test marking notification as read"""
    # Create notification
    notif = Notification(
        user_id=user_id,
        type=NotificationType.BOOKING_REQUEST,
        channel=NotificationChannel.BOTH,
        title="Test",
        message="Test message",
        read=False
    )
    db_session.add(notif)
    await db_session.commit()

    service = NotificationService(db_session)

    # Mark as read
    updated = await service.mark_as_read(notif.id, user_id)

    assert updated.read is True
    assert updated.read_at is not None


@pytest.mark.asyncio
async def test_notification_preference_get_channels():
    """Test getting enabled channels for notification type"""
    prefs = NotificationPreference(
        user_id=uuid4(),
        booking_requests_email=True,
        booking_requests_push=False,
        booking_updates_email=False,
        booking_updates_push=True
    )

    # Booking request: only email enabled
    channels = prefs.get_channels_for_type('booking_request')
    assert channels == ['email']

    # Booking approved: only push enabled
    channels = prefs.get_channels_for_type('booking_approved')
    assert channels == ['push']


@pytest.mark.asyncio
async def test_email_failure_does_not_crash(
    db_session,
    user_id,
    mock_email_service,
    mock_push_service
):
    """Test that email failure doesn't crash notification creation"""
    # Mock email failure
    mock_email_service.send_email = AsyncMock(return_value=False)

    service = NotificationService(db_session)
    await service.get_or_create_preferences(user_id)

    # Send notification
    notification = await service.send_notification(
        user_id=user_id,
        user_email="test@example.com",
        fcm_token="test_token",
        notification_type=NotificationType.BOOKING_REQUEST,
        title="Test",
        message="Test message",
        email_content="<html>Email</html>"
    )

    # Notification created despite email failure
    assert notification.id is not None
    assert notification.email_sent is False
    assert notification.push_sent is True  # Push still succeeded


@pytest.mark.asyncio
async def test_push_failure_does_not_crash(
    db_session,
    user_id,
    mock_email_service,
    mock_push_service
):
    """Test that push failure doesn't crash notification creation"""
    # Mock push failure
    mock_push_service.send_push_to_user = AsyncMock(return_value=False)

    service = NotificationService(db_session)
    await service.get_or_create_preferences(user_id)

    # Send notification
    notification = await service.send_notification(
        user_id=user_id,
        user_email="test@example.com",
        fcm_token="test_token",
        notification_type=NotificationType.BOOKING_REQUEST,
        title="Test",
        message="Test message",
        email_content="<html>Email</html>"
    )

    # Notification created despite push failure
    assert notification.id is not None
    assert notification.email_sent is True  # Email succeeded
    assert notification.push_sent is False
