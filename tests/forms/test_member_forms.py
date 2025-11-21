"""Tests for member forms"""

import pytest
from app.forms.member_forms import ProfileForm


class TestProfileForm:
    def test_valid_data(self, app):
        with app.test_request_context():
            form = ProfileForm(data={"name": "Updated Name", "phone": "9876543210"})
            assert form.validate()

    def test_short_name(self, app):
        with app.test_request_context():
            form = ProfileForm(data={"name": "A", "phone": "9876543210"})
            assert not form.validate()
