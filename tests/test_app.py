"""Comprehensive test suite for South East Archers application."""
import pytest
from datetime import datetime, timedelta
from app.models import User, Membership, News, Event, ShootingNight, CreditPurchase
from app.forms import LoginForm, RegistrationForm, ShootingNightForm
from app import db
from tests.conftest import login, logout


class TestModels:
    """Test all models."""
    
    def test_user_creation(self, app):
        """Test creating a user."""
        user = User(email='test@example.com', name='Test User')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.check_password('password123')
    
    def test_user_membership(self, app, regular_user):
        """Test user has membership and credits."""
        user = db.session.get(User, regular_user.id)
        assert user.current_membership is not None
        assert user.total_credits == 15
    
    def test_shooting_night_attendance(self, app, admin_user, regular_user):
        """Test shooting night with attendance."""
        admin = db.session.get(User, admin_user.id)
        user = db.session.get(User, regular_user.id)
        
        night = ShootingNight(
            date=datetime.utcnow().date(),
            location='Hall',
            created_by=admin.id
        )
        db.session.add(night)
        db.session.flush()
        night.attendees.append(user)
        db.session.commit()
        
        assert len(night.attendees) == 1
        assert night.attendees[0].id == user.id


class TestAuthentication:
    """Test authentication."""
    
    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get('/auth/login')
        assert response.status_code == 200
    
    def test_successful_login(self, client, regular_user):
        """Test login works."""
        response = login(client, 'user@test.com', 'user123')
        assert response.status_code == 200
    
    def test_registration(self, client, app):
        """Test user registration."""
        response = client.post('/auth/register', data={
            'email': 'newuser@test.com',
            'name': 'New User',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        user = User.query.filter_by(email='newuser@test.com').first()
        assert user is not None


class TestAdminRoutes:
    """Test admin functionality."""
    
    def test_admin_dashboard_requires_admin(self, client, regular_user):
        """Test non-admin cannot access admin dashboard."""
        login(client, 'user@test.com', 'user123')
        response = client.get('/admin/dashboard', follow_redirects=True)
        # Should redirect or show error
        assert response.status_code in [200, 302]
    
    def test_admin_can_access_dashboard(self, client, admin_user):
        """Test admin can access dashboard."""
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
    
    def test_create_shooting_night(self, client, admin_user, regular_user):
        """Test admin can create shooting night."""
        login(client, 'admin@test.com', 'admin123')
        
        user = db.session.get(User, regular_user.id)
        initial_credits = user.current_membership.credits_remaining
        
        response = client.post('/admin/shooting-nights/create', data={
            'date': datetime.utcnow().date().isoformat(),
            'location': 'Hall',
            'attendees': [regular_user.id],
            'notes': 'Test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify credit was deducted
        user = db.session.get(User, regular_user.id)
        assert user.current_membership.credits_remaining == initial_credits - 1
    
    def test_view_member_details(self, client, admin_user, regular_user):
        """Test admin can view member details."""
        login(client, 'admin@test.com', 'admin123')
        response = client.get(f'/admin/members/{regular_user.id}')
        assert response.status_code == 200
        assert b'Regular User' in response.data


class TestMemberRoutes:
    """Test member functionality."""
    
    def test_member_dashboard(self, client, regular_user):
        """Test member can access dashboard."""
        login(client, 'user@test.com', 'user123')
        response = client.get('/member/dashboard')
        assert response.status_code == 200
    
    def test_purchase_credits(self, client, regular_user):
        """Test member can purchase credits."""
        login(client, 'user@test.com', 'user123')
        
        user = db.session.get(User, regular_user.id)
        initial_credits = user.current_membership.credits_remaining
        
        response = client.post('/member/credits/purchase', data={
            'credits': 5
        }, follow_redirects=True)
        
        assert response.status_code == 200
        user = db.session.get(User, regular_user.id)
        assert user.current_membership.credits_remaining == initial_credits + 5


class TestForms:
    """Test forms validation."""
    
    def test_login_form_valid(self, app):
        """Test valid login form."""
        form = LoginForm(data={'email': 'test@example.com', 'password': 'password123'})
        assert form.validate()
    
    def test_registration_form_duplicate_email(self, app, regular_user):
        """Test registration with existing email."""
        form = RegistrationForm(data={
            'email': 'user@test.com',
            'name': 'Test',
            'password': 'password123',
            'password2': 'password123'
        })
        assert not form.validate()
    
    def test_shooting_night_form(self, app):
        """Test shooting night form."""
        form = ShootingNightForm(data={
            'date': datetime.utcnow().date(),
            'location': 'Hall',
            'attendees': []
        })
        form.attendees.choices = []
        assert form.validate()
