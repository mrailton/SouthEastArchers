"""Tests for admin forms"""
import pytest
from app.forms.admin_forms import ShootingNightForm, NewsForm, EventForm
from datetime import datetime


class TestShootingNightForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = ShootingNightForm(data={
                'date': datetime(2025, 12, 1, 18, 0),
                'location': 'Main Range',
                'description': 'Regular shooting night',
                'capacity': 20
            })
            assert form.validate()


class TestNewsForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = NewsForm(data={
                'title': 'Club News Article',
                'content': 'This is some news content that is long enough to pass validation',
                'summary': 'News summary'
            })
            assert form.validate()


class TestEventForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = EventForm(data={
                'title': 'Club Championship',
                'description': 'Annual club championship event',
                'start_date': datetime(2025, 12, 15, 10, 0),
                'location': 'Main Venue'
            })
            assert form.validate()
