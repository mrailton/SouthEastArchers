"""Tests for admin dashboard"""
import pytest


class TestAdminDashboard:
    def test_dashboard_requires_admin(self, client, test_user):
        """Test that dashboard requires admin"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code in [302, 403]

    def test_dashboard_with_admin(self, client, admin_user):
        """Test dashboard access with admin"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
