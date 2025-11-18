import pytest
import os
from app import create_app, db
from app.models import User, Membership
from datetime import date, timedelta


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    user = User(
        name='Test User',
        email='test@example.com',
        phone='1234567890',
        date_of_birth=date(2000, 1, 1)
    )
    user.set_password('password123')
    
    membership = Membership(
        user_id=None,
        start_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=335),
        credits=20,
        status='active'
    )
    
    db.session.add(user)
    db.session.flush()
    
    membership.user_id = user.id
    db.session.add(membership)
    db.session.commit()
    
    return user


@pytest.fixture
def test_admin(app):
    """Create a test admin user"""
    user = User(
        name='Admin User',
        email='admin@example.com',
        date_of_birth=date(2000, 1, 1),
        is_admin=True
    )
    user.set_password('admin123')
    db.session.add(user)
    db.session.commit()
    
    return user


@pytest.fixture
def admin_user(app):
    """Alias for test_admin for consistency"""
    user = User(
        name='Admin User',
        email='admin@example.com',
        date_of_birth=date(2000, 1, 1),
        is_admin=True
    )
    user.set_password('adminpass')
    db.session.add(user)
    db.session.commit()
    
    return user
