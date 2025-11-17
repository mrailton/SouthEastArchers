"""Tests for admin routes"""
import pytest
from datetime import date, timedelta
from app.models import News, Event


class TestAdminRoutes:
    def test_dashboard_requires_admin(self, client, test_user):
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code in [302, 403]

    def test_dashboard_with_admin(self, client, admin_user):
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200

    def test_shooting_nights_list(self, client, admin_user):
        """Test viewing shooting nights list"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/shooting-nights')
        assert response.status_code == 200

    def test_news_list(self, client, admin_user):
        """Test viewing news list"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/news')
        assert response.status_code == 200

    def test_events_list(self, client, admin_user):
        """Test viewing events list"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/events')
        assert response.status_code == 200

    def test_create_news_page(self, client, admin_user):
        """Test accessing create news page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/news/create')
        assert response.status_code == 200

    def test_create_event_page(self, client, admin_user):
        """Test accessing create event page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/events/create')
        assert response.status_code == 200

    def test_create_shooting_night(self, client, admin_user):
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post('/admin/shooting-nights/create', data={
            'date': '2025-12-25',
            'location': 'Main Range',
            'description': 'Christmas shoot',
            'capacity': 15
        }, follow_redirects=True)
        
        assert response.status_code == 200
