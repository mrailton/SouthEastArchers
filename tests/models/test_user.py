"""Tests for user model"""

import pytest
from app.models import User
from datetime import date


class TestUser:
    def test_create_user(self, app):
        from app import db

        user = User(
            name="John Doe", email="john@example.com", date_of_birth=date(2000, 1, 1)
        )
        user.set_password("password")

        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.email == "john@example.com"

    def test_password_hashing(self, test_user):
        assert not test_user.password_hash == "password123"
        assert test_user.check_password("password123")
        assert not test_user.check_password("wrongpassword")

    def test_get_age(self, test_user):
        age = test_user.get_age()
        assert isinstance(age, int)
        assert age >= 23  # Test user was born in 2000
