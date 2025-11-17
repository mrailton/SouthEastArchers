"""Tests for event model"""
import pytest
from app.models import Event
from datetime import date, timedelta


class TestEvent:
    def test_create_event(self, app):
        from app import db
        event = Event(
            title='Test Event',
            description='Test description',
            start_date=date.today() + timedelta(days=7),
            published=True
        )
        db.session.add(event)
        db.session.commit()
        
        assert event.id is not None
        assert event.title == 'Test Event'
        assert event.published is True
