"""Tests for shooting night model"""
import pytest
from app.models import ShootingNight, User
from datetime import date, timedelta, datetime


class TestShootingNight:
    def test_create_shooting_night(self, app):
        from app import db
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        assert night.id is not None
        assert night.location == 'Test Range'
        assert night.capacity == 10

    def test_is_full_false(self, app):
        """Test is_full returns False when not at capacity"""
        from app import db
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        assert not night.is_full()

    def test_is_full_true(self, app):
        """Test is_full returns True when at capacity"""
        from app import db
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=1
        )
        db.session.add(night)
        db.session.flush()
        
        # Add a user to fill capacity
        user = User(
            name='Test User',
            email='test@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        night.users.append(user)
        db.session.commit()
        
        assert night.is_full()

    def test_spots_remaining(self, app):
        """Test spots_remaining calculation"""
        from app import db
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.commit()
        
        assert night.spots_remaining() == 10

    def test_spots_remaining_with_attendees(self, app):
        """Test spots_remaining with attendees"""
        from app import db
        night = ShootingNight(
            date=date.today() + timedelta(days=7),
            location='Test Range',
            capacity=10
        )
        db.session.add(night)
        db.session.flush()
        
        user = User(
            name='Test User',
            email='test@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        night.users.append(user)
        db.session.commit()
        
        assert night.spots_remaining() == 9
