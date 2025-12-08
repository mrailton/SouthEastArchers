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
        response = client.post("/auth/login", data={"email": test_user.email, "password": "wrongpassword"})
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
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

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

    def test_logout_without_login(self, client):
        """Test logout without being logged in"""
        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
