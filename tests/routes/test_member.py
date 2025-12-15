"""Tests for member routes"""

from datetime import date, timedelta

import pytest

from app.models import Shoot, ShootLocation


class TestMemberRoutes:
    def test_dashboard_requires_login(self, client):
        response = client.get("/member/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_dashboard_logged_in(self, client, test_user):
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/member/dashboard")
        assert response.status_code == 200
        assert b"Credits Remaining" in response.data

    def test_view_shoots_history(self, client, test_user, app):
        from app import db

        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        # Create a shoot the user attended
        shoot = Shoot(date=date.today() - timedelta(days=7), location=ShootLocation.HALL)
        db.session.add(shoot)
        db.session.flush()

        shoot.users.append(test_user)
        db.session.commit()

        response = client.get("/member/shoots")
        assert response.status_code == 200

    def test_view_profile(self, client, test_user):
        """Test viewing profile page"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/member/profile")
        assert response.status_code == 200

    def test_update_profile(self, client, test_user):
        """Test updating profile"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.post(
            "/member/profile/update",
            data={"name": "Updated Name", "phone": "9876543210"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_change_password_page(self, client, test_user):
        """Test viewing change password page"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/member/change-password")
        assert response.status_code == 200

    def test_change_password_success(self, client, test_user):
        """Test changing password successfully"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.post(
            "/member/change-password",
            data={
                "current_password": "password123",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, test_user):
        """Test changing password with wrong current password"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.post(
            "/member/change-password",
            data={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
        )
        assert response.status_code == 200
        assert b"incorrect" in response.data.lower()

    def test_change_password_mismatch(self, client, test_user):
        """Test changing password with mismatched new passwords"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.post(
            "/member/change-password",
            data={
                "current_password": "password123",
                "new_password": "newpassword123",
                "confirm_password": "differentpassword",
            },
        )
        assert response.status_code == 200
        assert b"do not match" in response.data.lower()

    def test_view_credits_page(self, client, test_user):
        """Test viewing credits page"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/member/credits")
        assert response.status_code == 200

    def test_shoots_with_no_history(self, client, test_user):
        """Test shoots page when user has no shoot history"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/member/shoots")
        assert response.status_code == 200

    def test_update_profile_partial_data(self, client, test_user):
        """Test updating profile with partial data"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        # Only update name
        response = client.post(
            "/member/profile/update",
            data={"name": "Only Name Update"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify update
        from app import db

        db.session.refresh(test_user)
        assert test_user.name == "Only Name Update"

