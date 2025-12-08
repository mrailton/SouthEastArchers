"""Tests for event model"""

from datetime import datetime, timedelta

import pytest

from app.models import Event
from app.utils.datetime_utils import utc_now


class TestEvent:
    def test_create_event(self, app):
        """Test creating a basic event"""
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=datetime.now() + timedelta(days=7),
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        assert event.id is not None
        assert event.title == "Test Event"
        assert event.description == "Test description"
        assert event.published is True
        assert event.created_at is not None

    def test_create_event_with_end_date(self, app):
        """Test creating an event with end date"""
        from app import db

        start = datetime.now() + timedelta(days=7)
        end = start + timedelta(hours=3)

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=start,
            end_date=end,
            published=False,
        )
        db.session.add(event)
        db.session.commit()

        assert event.end_date == end
        assert event.end_date > event.start_date

    def test_create_event_with_location(self, app):
        """Test creating an event with location"""
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=datetime.now() + timedelta(days=7),
            location="Test Location",
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        assert event.location == "Test Location"

    def test_create_event_with_capacity(self, app):
        """Test creating an event with capacity limit"""
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=datetime.now() + timedelta(days=7),
            capacity=50,
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        assert event.capacity == 50

    def test_is_upcoming_future_event(self, app):
        """Test is_upcoming returns True for future event"""
        from datetime import datetime

        from app import db

        # Use a date far in the future to avoid timezone issues
        future_date = datetime(2030, 12, 31, 12, 0, 0)
        event = Event(
            title="Future Event",
            description="Test description",
            start_date=future_date,
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        assert event.is_upcoming() is True

    def test_is_upcoming_past_event(self, app):
        """Test is_upcoming returns False for past event"""
        from datetime import datetime

        from app import db

        # Use a date in the past
        past_date = datetime(2020, 1, 1, 12, 0, 0)
        event = Event(
            title="Past Event",
            description="Test description",
            start_date=past_date,
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        assert event.is_upcoming() is False

    def test_publish_event(self, app):
        """Test publishing an event"""
        from app import db

        event = Event(
            title="Unpublished Event",
            description="Test description",
            start_date=datetime.now() + timedelta(days=7),
            published=False,
        )
        db.session.add(event)
        db.session.commit()

        assert event.published is False

        event.publish()
        db.session.commit()

        assert event.published is True

    def test_event_repr(self, app):
        """Test event string representation"""
        from app import db

        start_date = datetime.now() + timedelta(days=7)
        event = Event(
            title="Test Event",
            description="Test description",
            start_date=start_date,
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        repr_str = repr(event)
        assert "Test Event" in repr_str
        assert "Event" in repr_str

    def test_is_upcoming_with_naive_datetime(self, app):
        """Test is_upcoming with naive datetime (no timezone)"""
        from datetime import datetime, timezone

        from app import db

        # Create event with naive datetime (no timezone info)
        future_date = datetime(2030, 12, 31, 12, 0, 0)  # Naive datetime
        event = Event(
            title="Future Event Naive",
            description="Test description",
            start_date=future_date,
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        # Should handle timezone conversion and return True for future date
        assert event.is_upcoming() is True

    def test_is_upcoming_with_aware_datetime(self, app):
        """Test is_upcoming with timezone-aware datetime"""
        from datetime import datetime, timezone

        from app import db

        # Create event with timezone-aware datetime
        future_date = datetime(2030, 12, 31, 12, 0, 0, tzinfo=timezone.utc)
        event = Event(
            title="Future Event Aware",
            description="Test description",
            start_date=future_date,
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        # Should handle timezone-aware datetime correctly
        assert event.is_upcoming() is True
