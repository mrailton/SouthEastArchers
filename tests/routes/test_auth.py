"""Tests for auth routes"""

from datetime import date

import pytest

from app.models import User


class TestAuthRoutes:
    def test_login_page_get(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_signup_page_get(self, client):
        response = client.get("/auth/signup")
        assert response.status_code == 200
        assert b"Sign Up" in response.data

    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials"""
        response = client.post(
            "/auth/login",
            data={"email": test_user.email, "password": "password123"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password"""
        response = client.post(
            "/auth/login", data={"email": test_user.email, "password": "wrongpassword"}
        )
        assert response.status_code == 200
        assert b"Invalid" in response.data

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent email"""
        response = client.post(
            "/auth/login",
            data={"email": "nonexistent@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        assert b"Invalid" in response.data

    def test_signup_new_user(self, client):
        """Test signup with new user"""
        response = client.post(
            "/auth/signup",
            data={
                "name": "New User",
                "email": "newuser@example.com",
                "phone": "1234567890",
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_signup_existing_email(self, client, test_user):
        """Test signup with existing email"""
        response = client.post(
            "/auth/signup",
            data={
                "name": "Another User",
                "email": test_user.email,
                "phone": "1234567890",
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
        )
        assert response.status_code == 200

    def test_logout(self, client, test_user):
        client.post(
            "/auth/login", data={"email": test_user.email, "password": "password123"}
        )

        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200

    def test_login_inactive_user(self, client, app):
        from app import db

        user = User(
            name="Inactive User",
            email="inactive@example.com",
            date_of_birth=date(2000, 1, 1),
            is_active=False,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        response = client.post(
            "/auth/login",
            data={"email": "inactive@example.com", "password": "password123"},
        )
        assert response.status_code == 200

    def test_login_with_next_parameter(self, client, test_user):
        """Test login redirects to next parameter"""
        response = client.post(
            "/auth/login?next=/member/profile",
            data={"email": test_user.email, "password": "password123"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/member/profile" in response.location

    def test_login_remember_me(self, client, test_user):
        """Test login with remember me checkbox"""
        response = client.post(
            "/auth/login",
            data={
                "email": test_user.email,
                "password": "password123",
                "remember": True,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_signup_password_mismatch(self, client):
        """Test signup with mismatched passwords"""
        response = client.post(
            "/auth/signup",
            data={
                "name": "New User",
                "email": "newuser@example.com",
                "phone": "1234567890",
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "differentpassword",
                "payment_method": "cash",
            },
        )
        assert response.status_code == 200
        assert b"do not match" in response.data

    def test_signup_invalid_date(self, client):
        """Test signup with invalid date of birth"""
        response = client.post(
            "/auth/signup",
            data={
                "name": "New User",
                "email": "newuser@example.com",
                "phone": "1234567890",
                "date_of_birth": "invalid-date",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
        )
        assert response.status_code == 200
        assert b"Invalid date" in response.data

    def test_signup_missing_fields(self, client):
        """Test signup with missing required fields"""
        response = client.post(
            "/auth/signup",
            data={
                "name": "New User",
                "email": "",  # Missing email
                "date_of_birth": "2000-01-01",
                "password": "password123",
                "password_confirm": "password123",
                "payment_method": "cash",
            },
        )
        assert response.status_code == 200
        assert b"required" in response.data.lower()

    def test_signup_online_payment(self, client, app):
        """Test signup with online payment method"""
        from unittest.mock import Mock, patch

        with patch("app.routes.auth.SumUpService") as mock_service_class:
            mock_service = Mock()
            mock_checkout = {"id": "checkout_signup", "status": "PENDING"}
            mock_service.create_checkout.return_value = mock_checkout
            mock_service_class.return_value = mock_service

            response = client.post(
                "/auth/signup",
                data={
                    "name": "Online User",
                    "email": "online@example.com",
                    "phone": "1234567890",
                    "date_of_birth": "2000-01-01",
                    "password": "password123",
                    "password_confirm": "password123",
                    "payment_method": "online",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert "/payment/checkout/" in response.location

    def test_signup_online_payment_failure(self, client, app):
        """Test signup when online payment checkout creation fails"""
        from unittest.mock import Mock, patch

        with patch("app.routes.auth.SumUpService") as mock_service_class:
            mock_service = Mock()
            mock_service.create_checkout.return_value = None
            mock_service_class.return_value = mock_service

            response = client.post(
                "/auth/signup",
                data={
                    "name": "Online User",
                    "email": "online2@example.com",
                    "phone": "1234567890",
                    "date_of_birth": "2000-01-01",
                    "password": "password123",
                    "password_confirm": "password123",
                    "payment_method": "online",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"Error creating payment" in response.data

    def test_forgot_password_get(self, client):
        """Test forgot password page GET"""
        response = client.get("/auth/forgot-password")
        assert response.status_code == 200
        assert b"Forgot Password" in response.data or b"forgot" in response.data.lower()

    def test_forgot_password_existing_user(self, client, test_user, app):
        """Test forgot password with existing user"""
        from unittest.mock import patch

        with patch("app.routes.auth.mail.send") as mock_send:
            response = client.post(
                "/auth/forgot-password",
                data={"email": test_user.email},
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"receive a password reset link" in response.data

    def test_forgot_password_nonexistent_user(self, client):
        """Test forgot password with nonexistent user"""
        response = client.post(
            "/auth/forgot-password",
            data={"email": "nonexistent@example.com"},
            follow_redirects=True,
        )

        # Should still show success message for security
        assert response.status_code == 200
        assert b"receive a password reset link" in response.data

    def test_forgot_password_email_failure(self, client, test_user, app):
        """Test forgot password when email sending fails"""
        from unittest.mock import patch

        with patch(
            "app.routes.auth.mail.send", side_effect=Exception("Email error")
        ):
            response = client.post(
                "/auth/forgot-password", data={"email": test_user.email}
            )

            assert response.status_code == 200
            assert b"error" in response.data.lower()

    def test_reset_password_get_valid_token(self, client, test_user):
        """Test reset password page with valid token"""
        token = test_user.generate_reset_token()
        response = client.get(f"/auth/reset-password/{token}")
        assert response.status_code == 200
        assert (
            b"Reset Password" in response.data or b"password" in response.data.lower()
        )

    def test_reset_password_invalid_token(self, client):
        """Test reset password with invalid token"""
        response = client.get(
            "/auth/reset-password/invalid_token", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Invalid" in response.data or b"expired" in response.data.lower()

    def test_reset_password_success(self, client, test_user):
        """Test successful password reset"""
        token = test_user.generate_reset_token()
        response = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "newpassword123", "password_confirm": "newpassword123"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert (
            b"successfully" in response.data.lower()
            or b"login" in response.data.lower()
        )

    def test_reset_password_mismatch(self, client, test_user):
        """Test reset password with mismatched passwords"""
        token = test_user.generate_reset_token()
        response = client.post(
            f"/auth/reset-password/{token}",
            data={
                "password": "newpassword123",
                "password_confirm": "differentpassword",
            },
        )

        assert response.status_code == 200
        assert b"do not match" in response.data

    def test_reset_password_too_short(self, client, test_user):
        """Test reset password with too short password"""
        token = test_user.generate_reset_token()
        response = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "short", "password_confirm": "short"},
        )

        assert response.status_code == 200
        assert b"at least 8 characters" in response.data

    def test_reset_password_missing_fields(self, client, test_user):
        """Test reset password with missing fields"""
        token = test_user.generate_reset_token()
        response = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "", "password_confirm": ""},
        )

        assert response.status_code == 200
        assert b"fill in all fields" in response.data.lower()

    def test_logout_without_login(self, client):
        """Test logout without being logged in"""
        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
