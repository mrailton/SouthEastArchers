"""Tests for user model"""

from datetime import date

import pytest

from app.models import User


class TestUser:
    def test_password_hashing(self, test_user):
        assert not test_user.password_hash == "password123"
        assert test_user.check_password("password123")
        assert not test_user.check_password("wrongpassword")

    def test_get_age(self, test_user):
        age = test_user.get_age()
        assert isinstance(age, int)
        assert age >= 23  # Test user was born in 2000
