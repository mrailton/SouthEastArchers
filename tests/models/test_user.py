"""Tests for user model"""

from datetime import date

import pytest

from app.models import User


class TestUser:
    def test_create_user(self, app):
        from app import db

        user = User(name="John Doe", email="john@example.com", date_of_birth=date(2000, 1, 1))
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

    def test_user_repr(self, test_user):
        """Test user string representation"""
        repr_str = repr(test_user)
        assert "User" in repr_str
        assert test_user.email in repr_str
