from unittest.mock import patch

import pytest
from flask import url_for

from app import db
from app.models import User


class TestPasswordReset:
    """Tests for password reset functionality"""

    def test_forgot_password_page_loads(self, client):
        """Test that forgot password page loads"""
        response = client.get("/auth/forgot-password")
        assert response.status_code == 200
        assert b"Forgot Password" in response.data or b"Reset Password" in response.data

    @patch("app.utils.email.mail.send")
    def test_forgot_password_with_valid_email(self, mock_mail_send, client, test_user):
        """Test forgot password with valid email"""
        response = client.post(
            "/auth/forgot-password",
            data={"email": test_user.email},
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Check for the actual flash message
        assert b"password reset link" in response.data.lower() or b"if an account exists" in response.data.lower()
        # Verify email was attempted to be sent
        assert mock_mail_send.called

    @patch("app.utils.email.mail.send")
    def test_forgot_password_with_invalid_email(self, mock_mail_send, client):
        """Test forgot password with non-existent email"""
        response = client.post(
            "/auth/forgot-password",
            data={"email": "nonexistent@example.com"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Same message for security (don't reveal if email exists)
        assert b"password reset link" in response.data.lower() or b"if an account exists" in response.data.lower()
        # Email should not be sent for non-existent user
        assert not mock_mail_send.called

    def test_generate_reset_token(self, app, test_user):
        """Test that user can generate a reset token"""
        with app.app_context():
            token = test_user.generate_reset_token()
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

    def test_verify_valid_reset_token(self, app, test_user):
        """Test verifying a valid reset token"""
        with app.app_context():
            token = test_user.generate_reset_token()
            user = User.verify_reset_token(token)
            assert user is not None
            assert user.id == test_user.id
            assert user.email == test_user.email

    def test_verify_invalid_reset_token(self, app):
        """Test verifying an invalid reset token"""
        with app.app_context():
            user = User.verify_reset_token("invalid-token")
            assert user is None

    def test_verify_expired_reset_token(self, app, test_user):
        """Test verifying an expired reset token"""
        import time

        with app.app_context():
            token = test_user.generate_reset_token()
            # Wait a moment to ensure time has passed
            time.sleep(0.1)
            # Verify with very short max_age to simulate expiry
            user = User.verify_reset_token(token, max_age=-1)
            assert user is None

    def test_reset_password_with_invalid_token(self, client):
        """Test reset password page with invalid token"""
        response = client.get("/auth/reset-password/invalid-token")
        assert response.status_code == 302  # Redirect

        response = client.get("/auth/reset-password/invalid-token", follow_redirects=True)
        assert b"Invalid or expired" in response.data

    def test_reset_password_with_valid_token(self, app, client, test_user):
        """Test reset password page with valid token"""
        with app.app_context():
            token = test_user.generate_reset_token()

        response = client.get(f"/auth/reset-password/{token}")
        assert response.status_code == 200
        assert b"Reset Password" in response.data or b"New Password" in response.data

    def test_reset_password_success(self, app, client, test_user):
        """Test successful password reset"""
        with app.app_context():
            token = test_user.generate_reset_token()
            old_password_hash = test_user.password_hash

        new_password = "NewSecurePassword123!"
        response = client.post(
            f"/auth/reset-password/{token}",
            data={"password": new_password, "password_confirm": new_password},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Password reset successfully" in response.data

        with app.app_context():
            user = db.session.get(User, test_user.id)
            assert user.password_hash != old_password_hash
            assert user.check_password(new_password)

