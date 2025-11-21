"""Tests for admin forms"""

from datetime import date, timedelta

import pytest

from app.forms.admin_forms import EventForm, NewsForm, ShootForm


class TestShootForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = ShootForm(
                data={
                    "date": date.today(),
                    "location": "HALL",
                    "description": "Test shoot",
                }
            )
            assert form.validate()


class TestNewsForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = NewsForm(
                data={
                    "title": "Club News Article",
                    "content": "This is some news content that is long enough to pass validation",
                    "summary": "News summary",
                }
            )
            assert form.validate()


class TestEventForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = EventForm(
                data={
                    "title": "Club Championship",
                    "description": "Annual club championship event",
                    "start_date": date.today() + timedelta(days=30),
                    "location": "Main Venue",
                }
            )
            assert form.validate()
