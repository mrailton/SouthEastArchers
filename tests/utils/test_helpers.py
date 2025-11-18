"""Tests for helpers"""
import pytest
from app.utils.helpers import get_user_or_404
from werkzeug.exceptions import NotFound


class TestGetUserOr404:
    def test_returns_user_when_exists(self, app, test_user):
        """Test that get_user_or_404 returns user when they exist"""
        with app.app_context():
            user = get_user_or_404(test_user.id)
            assert user.id == test_user.id
            assert user.email == test_user.email
    
    def test_raises_404_when_not_exists(self, app):
        """Test that get_user_or_404 raises 404 when user doesn't exist"""
        with app.app_context():
            with pytest.raises(NotFound):
                get_user_or_404(99999)
