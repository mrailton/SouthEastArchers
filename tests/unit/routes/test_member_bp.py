"""Tests for member routes"""
import pytest
from datetime import date, timedelta
from app.models import ShootingNight, Credit


class TestMemberRoutes:
    def test_dashboard_requires_login(self, client):
        response = client.get('/member/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_dashboard_logged_in(self, client, test_user):
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/member/dashboard')
        assert response.status_code == 200

    def test_view_shooting_nights(self, client, test_user, app):
        from app import db
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        response = client.get('/member/shooting-nights')
        assert response.status_code == 200

    def test_register_for_shooting_night(self, client, test_user, app):
        """Test registering for a shooting night"""
        from app import db
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        response = client.post(f'/member/shooting-nights/{night.id}/register', 
                              follow_redirects=True)
        assert response.status_code == 200

    def test_register_for_full_shooting_night(self, client, test_user, app):
        """Test registering for a full shooting night"""
        from app import db
        from app.models import User
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        # Create a full shooting night
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=1
        )
        db.session.add(night)
        db.session.flush()
        
        # Register another user to fill it
        other_user = User(
            name='Other User',
            email='other@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        other_user.set_password('password')
        db.session.add(other_user)
        db.session.flush()
        
        night.users.append(other_user)
        db.session.commit()
        
        response = client.post(f'/member/shooting-nights/{night.id}/register',
                              follow_redirects=True)
        assert response.status_code == 200
        assert b'full' in response.data.lower()

    def test_register_twice_for_same_night(self, client, test_user, app):
        """Test registering twice for the same night"""
        from app import db
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        # Register first time
        client.post(f'/member/shooting-nights/{night.id}/register')
        
        # Try to register again
        response = client.post(f'/member/shooting-nights/{night.id}/register',
                              follow_redirects=True)
        assert response.status_code == 200
        assert b'already registered' in response.data.lower()

    def test_register_with_credits(self, client, test_user, app):
        """Test registering using credits"""
        from app import db
        
        # Use up membership nights
        test_user.membership.nights_used = 12
        
        # Add credits
        credit = Credit(user_id=test_user.id, amount=5, used=0)
        db.session.add(credit)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        response = client.post(f'/member/shooting-nights/{night.id}/register',
                              follow_redirects=True)
        assert response.status_code == 200

    def test_view_credits_page(self, client, test_user):
        """Test viewing credits page"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/member/credits')
        assert response.status_code == 200

    def test_view_profile(self, client, test_user):
        """Test viewing profile page"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/member/profile')
        assert response.status_code == 200

    def test_update_profile(self, client, test_user):
        """Test updating profile"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.post('/member/profile/update', data={
            'name': 'Updated Name',
            'phone': '9876543210'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_change_password_page(self, client, test_user):
        """Test viewing change password page"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/member/change-password')
        assert response.status_code == 200

    def test_change_password_success(self, client, test_user):
        """Test changing password successfully"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.post('/member/change-password', data={
            'current_password': 'password123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'successfully' in response.data.lower()

    def test_change_password_wrong_current(self, client, test_user):
        """Test changing password with wrong current password"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.post('/member/change-password', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        assert response.status_code == 200
        assert b'incorrect' in response.data.lower()

    def test_change_password_mismatch(self, client, test_user):
        """Test changing password with mismatched new passwords"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.post('/member/change-password', data={
            'current_password': 'password123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        })
        assert response.status_code == 200
        assert b'do not match' in response.data.lower()
