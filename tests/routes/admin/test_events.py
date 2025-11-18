"""Tests for admin event management"""
import pytest
from datetime import datetime
from app.models import Event


class TestAdminEvents:
    def test_events_list(self, client, admin_user):
        """Test viewing events list"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/events')
        assert response.status_code == 200

    def test_create_event_page(self, client, admin_user):
        """Test accessing create event page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/events/create')
        assert response.status_code == 200

    def test_edit_event_page(self, client, admin_user, app):
        """Test accessing edit event page"""
        from app import db
        
        event = Event(
            title='Test Event',
            description='Test description',
            start_date=datetime.now(),
            published=False
        )
        db.session.add(event)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get(f'/admin/events/{event.id}/edit')
        assert response.status_code == 200
        assert b'Edit Event' in response.data
        assert b'Test Event' in response.data

    def test_edit_event_success(self, client, admin_user, app):
        """Test updating event"""
        from app import db
        
        event = Event(
            title='Original Event',
            description='Original description',
            start_date=datetime.now(),
            published=False
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        new_date = datetime.now().strftime('%Y-%m-%dT%H:%M')
        response = client.post(f'/admin/events/{event_id}/edit', data={
            'title': 'Updated Event',
            'description': 'Updated description',
            'start_date': new_date,
            'location': 'New Location',
            'published': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify changes
        updated_event = db.session.get(Event, event_id)
        assert updated_event.title == 'Updated Event'
        assert updated_event.location == 'New Location'
        assert updated_event.published is True

    def test_edit_event_not_found(self, client, admin_user):
        """Test editing non-existent event"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/events/99999/edit')
        assert response.status_code == 404

    def test_events_requires_admin(self, client, test_user):
        """Test that events require admin"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/admin/events')
        assert response.status_code in [302, 403]
