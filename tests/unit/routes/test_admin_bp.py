"""Tests for admin routes"""
import pytest
from datetime import date, timedelta
from app.models import Shoot, ShootLocation


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

    def test_shoots_list(self, client, admin_user):
        """Test viewing shoots list"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/shoots')
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

    def test_create_shoot_page(self, client, admin_user):
        """Test accessing create shoot page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/shoots/create')
        assert response.status_code == 200

    def test_edit_shoot_page(self, client, admin_user, app):
        """Test accessing edit shoot page"""
        from app import db
        from app.models import Shoot, ShootLocation
        from datetime import date
        
        # Create a shoot first
        shoot = Shoot(
            date=date.today(),
            location=ShootLocation.HALL,
            description='Test shoot'
        )
        db.session.add(shoot)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get(f'/admin/shoots/{shoot.id}/edit')
        assert response.status_code == 200
        assert b'Edit Shoot' in response.data

    def test_edit_shoot_updates_details(self, client, admin_user, app):
        """Test updating shoot details"""
        from app import db
        from app.models import Shoot, ShootLocation
        from datetime import date
        
        # Create a shoot
        shoot = Shoot(
            date=date.today(),
            location=ShootLocation.HALL,
            description='Original description'
        )
        db.session.add(shoot)
        db.session.commit()
        shoot_id = shoot.id
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        # Update the shoot
        response = client.post(f'/admin/shoots/{shoot_id}/edit', data={
            'date': date.today().isoformat(),
            'location': 'MEADOW',
            'description': 'Updated description',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
