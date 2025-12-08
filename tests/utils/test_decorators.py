"""Tests for decorators"""

import pytest
from flask import session


class TestLoginRequired:
    def test_redirects_when_not_logged_in(self, client):
        """Test that login_required redirects to login when not authenticated"""
        response = client.get("/member/dashboard")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_allows_access_when_logged_in(self, client, test_user):
        """Test that login_required allows access when authenticated"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/member/dashboard")
        assert response.status_code == 200


class TestAdminRequired:
    def test_redirects_when_not_logged_in(self, client):
        """Test that admin_required redirects when not authenticated"""
        response = client.get("/admin/dashboard")
        assert response.status_code == 302

    def test_redirects_when_not_admin(self, client, test_user):
        """Test that admin_required redirects when user is not admin"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/admin/dashboard")
        assert response.status_code in [302, 403]

    def test_allows_access_for_admin(self, client, admin_user):
        """Test that admin_required allows access for admin users"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/dashboard")
        assert response.status_code == 200
