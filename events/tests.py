"""
Tests for the events app.
"""
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event
from events.forms import EventForm

User = get_user_model()


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.models
@pytest.mark.django_db
class TestEventModel:
    """Test the Event model."""

    def test_create_event(self, user):
        """Test creating an event."""
        event_date = timezone.now() + timedelta(days=7)
        event = Event.objects.create(
            title='Test Event',
            description='Test event description',
            event_date=event_date,
            location='Test Location',
            published=True,
            created_by=user
        )
        assert event.title == 'Test Event'
        assert event.description == 'Test event description'
        assert event.location == 'Test Location'
        assert event.published is True
        assert event.created_by == user

    def test_event_string_representation(self, event):
        """Test __str__ method returns title."""
        assert str(event) == 'Test Event'

    def test_event_ordering(self, user):
        """Test events are ordered by event_date descending."""
        future_event = Event.objects.create(
            title='Future Event',
            description='Future description',
            event_date=timezone.now() + timedelta(days=30),
            location='Future Location',
            published=True,
            created_by=user
        )

        near_event = Event.objects.create(
            title='Near Event',
            description='Near description',
            event_date=timezone.now() + timedelta(days=7),
            location='Near Location',
            published=True,
            created_by=user
        )

        events = list(Event.objects.all())
        assert events[0] == future_event  # Most distant date first
        assert events[1] == near_event

    def test_event_defaults(self, user):
        """Test default values for event."""
        event = Event.objects.create(
            title='Default Event',
            description='Description',
            event_date=timezone.now() + timedelta(days=1),
            location='Location',
            created_by=user
        )
        assert event.published is True  # Default published


# ============================================================================
# FORM TESTS
# ============================================================================

@pytest.mark.forms
@pytest.mark.django_db
class TestEventForm:
    """Test the EventForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form = EventForm(data={
            'title': 'Test Event',
            'description': 'Test description',
            'event_date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Test Location',
            'published': True
        })
        assert form.is_valid()

    def test_missing_required_fields(self):
        """Test form validation fails with missing required fields."""
        form = EventForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'event_date' in form.errors

    def test_unpublished_event(self):
        """Test creating unpublished event."""
        form = EventForm(data={
            'title': 'Draft Event',
            'description': 'Draft description',
            'event_date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Test Location',
            'published': False
        })
        assert form.is_valid()
        assert form.cleaned_data['published'] is False


# ============================================================================
# ADMIN TESTS
# ============================================================================

@pytest.mark.admin
@pytest.mark.django_db
class TestEventAdmin:
    """Test Event admin functionality."""

    def test_admin_list_view(self, admin_client):
        """Test admin can view events list."""
        response = admin_client.get('/admin/events/event/')
        assert response.status_code == 200

    def test_admin_can_create_event(self, admin_client, admin_user):
        """Test admin can create event."""
        event_date = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        response = admin_client.post('/admin/events/event/add/', {
            'title': 'Admin Created Event',
            'description': 'Description by admin.',
            'event_date': event_date,
            'location': 'Admin Location',
            'published': True,
            'created_by': admin_user.id
        })
        assert response.status_code in [200, 302]

    def test_admin_filter_by_published(self, admin_client, event, user):
        """Test admin can filter events by published status."""
        # Create unpublished event
        Event.objects.create(
            title='Unpublished Event',
            description='Description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=False,
            created_by=user
        )

        response = admin_client.get('/admin/events/event/', {'published__exact': '1'})
        assert response.status_code == 200
        assert event.title.encode() in response.content

    def test_admin_auto_sets_created_by(self, admin_client, admin_user):
        """Test admin automatically sets created_by on new event."""
        from events.admin import EventAdmin
        from django.contrib.admin.sites import AdminSite
        from unittest.mock import Mock

        admin = EventAdmin(Event, AdminSite())
        event_date = timezone.now() + timedelta(days=7)
        
        event = Event(
            title='Test Event',
            description='Description',
            event_date=event_date,
            location='Location',
            published=True
        )
        
        request = Mock()
        request.user = admin_user
        
        # Test save_model sets created_by on create
        admin.save_model(request, event, None, change=False)
        assert event.created_by == admin_user
