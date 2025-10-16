"""Pytest configuration and fixtures for testing."""
import pytest
import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Membership, News, Event, ShootingNight, CreditPurchase
from config import Config


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'


@pytest.fixture(scope='function')
def app():
    """Create and configure a test application instance."""
    # Force test environment variable to prevent accidental production DB usage
    os.environ['TESTING'] = '1'
    
    app = create_app(TestConfig)
    
    # Double-check we're using in-memory database
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:', \
        "Tests must use in-memory database!"
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        # Close the engine connection pool
        db.engine.pool.dispose()
    
    # Clean up environment variable
    os.environ.pop('TESTING', None)


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def admin_user(app):
    """Create an admin user."""
    user = User(
        email='admin@test.com',
        name='Admin User',
        phone='1234567890',
        is_admin=True
    )
    user.set_password('admin123')
    db.session.add(user)
    
    # Create membership
    membership = Membership(
        user=user,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=365),
        credits_remaining=20,
        amount_paid=100.0
    )
    db.session.add(membership)
    db.session.commit()
    
    # Refresh to avoid detached instance issues
    db.session.refresh(user)
    return user


@pytest.fixture(scope='function')
def regular_user(app):
    """Create a regular user."""
    user = User(
        email='user@test.com',
        name='Regular User',
        phone='0987654321',
        is_admin=False
    )
    user.set_password('user123')
    db.session.add(user)
    
    # Create membership
    membership = Membership(
        user=user,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=365),
        credits_remaining=15,
        amount_paid=100.0
    )
    db.session.add(membership)
    db.session.commit()
    
    # Refresh to avoid detached instance issues
    db.session.refresh(user)
    return user


@pytest.fixture(scope='function')
def multiple_users(app):
    """Create multiple users for testing."""
    users = []
    for i in range(3):
        user = User(
            email=f'user{i}@test.com',
            name=f'Test User {i}',
            phone=f'12345678{i}',
            is_admin=False
        )
        user.set_password('password123')
        db.session.add(user)
        
        membership = Membership(
            user=user,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            credits_remaining=10,
            amount_paid=100.0
        )
        db.session.add(membership)
        users.append(user)
    
    db.session.commit()
    
    # Refresh all users
    for user in users:
        db.session.refresh(user)
    return users


@pytest.fixture(scope='function')
def sample_news(app, admin_user):
    """Create sample news articles."""
    news_items = []
    for i in range(3):
        news = News(
            title=f'News Article {i}',
            content=f'Content for news article {i}',
            author_id=admin_user.id,
            published=True
        )
        db.session.add(news)
        news_items.append(news)
    
    db.session.commit()
    
    # Refresh all news items
    for news in news_items:
        db.session.refresh(news)
    return news_items


@pytest.fixture(scope='function')
def sample_event(app, admin_user):
    """Create a sample event."""
    event = Event(
        title='Test Event',
        description='Test event description',
        event_date=datetime.utcnow() + timedelta(days=7),
        location='Test Location',
        published=True,
        created_by=admin_user.id
    )
    db.session.add(event)
    db.session.commit()
    db.session.refresh(event)
    return event


@pytest.fixture(scope='function')
def sample_shooting_night(app, admin_user, regular_user):
    """Create a sample shooting night with attendance."""
    shooting_night = ShootingNight(
        date=datetime.utcnow().date(),
        location='Hall',
        notes='Test shooting night',
        created_by=admin_user.id
    )
    db.session.add(shooting_night)
    db.session.flush()
    
    # Add attendee
    shooting_night.attendees.append(regular_user)
    membership = regular_user.current_membership
    if membership:
        membership.credits_remaining -= 1
    
    db.session.commit()
    db.session.refresh(shooting_night)
    return shooting_night


def login(client, email, password):
    """Helper function to log in a user."""
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


def logout(client):
    """Helper function to log out a user."""
    return client.get('/auth/logout', follow_redirects=True)
