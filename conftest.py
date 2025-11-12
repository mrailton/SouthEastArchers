"""
Shared pytest fixtures for the SouthEast Archers project.
"""
import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        'email': 'test@example.com',
        'name': 'Test User',
        'phone': '1234567890',
        'password': 'TestPass123!'
    }


@pytest.fixture
def user(db, user_data):
    """Create and return a basic user."""
    user = User.objects.create_user(
        email=user_data['email'],
        name=user_data['name'],
        phone=user_data['phone'],
        password=user_data['password']
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_superuser(
        email='admin@example.com',
        name='Admin User',
        phone='0987654321',
        password='AdminPass123!'
    )


@pytest.fixture
def users(db):
    """Create multiple test users."""
    users_list = []
    for i in range(1, 6):
        user = User.objects.create_user(
            email=f'user{i}@example.com',
            name=f'User {i}',
            phone=f'12345{i:05d}',
            password='TestPass123!'
        )
        users_list.append(user)
    return users_list


@pytest.fixture
def membership(db, user):
    """Create an active membership for a user."""
    from memberships.models import Membership
    return Membership.objects.create(
        user=user,
        end_date=timezone.now() + timedelta(days=365),
        credits_remaining=20,
        is_active=True,
        amount_paid=100
    )


@pytest.fixture
def expired_membership(db, user):
    """Create an expired membership for a user."""
    from memberships.models import Membership
    return Membership.objects.create(
        user=user,
        end_date=timezone.now() - timedelta(days=1),
        credits_remaining=0,
        is_active=False,
        amount_paid=100
    )


@pytest.fixture
def credit_purchase(db, user):
    """Create a credit purchase record."""
    from memberships.models import CreditPurchase
    return CreditPurchase.objects.create(
        user=user,
        credits_purchased=10,
        amount_paid=50
    )


@pytest.fixture
def news_article(db, user):
    """Create a published news article."""
    from news.models import News
    return News.objects.create(
        title='Test News Article',
        content='This is test content for the news article.',
        author=user,
        published=True
    )


@pytest.fixture
def unpublished_news(db, user):
    """Create an unpublished news article."""
    from news.models import News
    return News.objects.create(
        title='Unpublished News',
        content='This is unpublished content.',
        author=user,
        published=False
    )


@pytest.fixture
def event(db, user):
    """Create a published event."""
    from events.models import Event
    return Event.objects.create(
        title='Test Event',
        description='Test event description',
        event_date=timezone.now() + timedelta(days=7),
        location='Test Location',
        published=True,
        created_by=user
    )


@pytest.fixture
def past_event(db, user):
    """Create a past event."""
    from events.models import Event
    return Event.objects.create(
        title='Past Event',
        description='Past event description',
        event_date=timezone.now() - timedelta(days=7),
        location='Past Location',
        published=True,
        created_by=user
    )


@pytest.fixture
def shooting_night(db, user):
    """Create a shooting night."""
    from shooting.models import ShootingNight
    return ShootingNight.objects.create(
        date=timezone.now().date(),
        location='Hall',
        notes='Test shooting night',
        created_by=user
    )


@pytest.fixture
def shooting_attendance(db, shooting_night, user):
    """Create a shooting attendance record."""
    from shooting.models import ShootingAttendance
    return ShootingAttendance.objects.create(
        shooting_night=shooting_night,
        user=user,
        credits_deducted=1
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return a logged-in Django test client."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return a logged-in admin Django test client."""
    client.force_login(admin_user)
    return client
