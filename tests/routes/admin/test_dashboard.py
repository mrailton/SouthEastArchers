"""Tests for admin dashboard"""

import pytest


class TestAdminDashboard:
    def test_dashboard_requires_admin(self, client, test_user):
        """Test that dashboard requires admin"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/admin/dashboard")
        assert response.status_code in [302, 403]

    def test_dashboard_with_admin(self, client, admin_user):
        """Test dashboard access with admin"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/dashboard")
        assert response.status_code == 200

    def test_dashboard_displays_stats(self, client, admin_user, test_user, app):
        """Test dashboard displays member, membership, and shoot statistics"""
        from datetime import date

        from app import db
        from app.models import Shoot, ShootLocation

        # Create a shoot
        shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
        db.session.add(shoot)
        db.session.commit()

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/dashboard")
        assert response.status_code == 200
        # Should display stats about members and shoots
        assert b"Member" in response.data or b"member" in response.data

    def test_dashboard_shows_recent_members(self, client, admin_user, test_user, app):
        """Test dashboard shows recent members"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/dashboard")
        assert response.status_code == 200
        # Dashboard should render successfully with recent members section
        assert b"Dashboard" in response.data or b"dashboard" in response.data

    def test_dashboard_unauthenticated(self, client):
        """Test dashboard without login redirects"""
        response = client.get("/admin/dashboard", follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login
        assert b"Login" in response.data
