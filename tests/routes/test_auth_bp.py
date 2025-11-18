"""Tests for auth routes"""
import pytest
from datetime import date
from app.models import User


class TestAuthRoutes:
    def test_login_page_get(self, client):
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_signup_page_get(self, client):
        response = client.get('/auth/signup')
        assert response.status_code == 200
        assert b'Sign Up' in response.data

    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials"""
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password"""
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'Invalid' in response.data

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent email"""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert b'Invalid' in response.data

    def test_signup_new_user(self, client):
        """Test signup with new user"""
        response = client.post('/auth/signup', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone': '1234567890',
            'date_of_birth': '2000-01-01',
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_signup_existing_email(self, client, test_user):
        """Test signup with existing email"""
        response = client.post('/auth/signup', data={
            'name': 'Another User',
            'email': test_user.email,
            'phone': '1234567890',
            'date_of_birth': '2000-01-01',
            'password': 'password123',
            'password_confirm': 'password123'
        })
        assert response.status_code == 200

    def test_logout(self, client, test_user):
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_login_inactive_user(self, client, app):
        from app import db
        user = User(
            name='Inactive User',
            email='inactive@example.com',
            date_of_birth=date(2000, 1, 1),
            is_active=False
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        response = client.post('/auth/login', data={
            'email': 'inactive@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
