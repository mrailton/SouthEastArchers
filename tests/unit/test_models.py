import pytest
from app.models import User, Membership, Credit
from datetime import date, timedelta


class TestUser:
    def test_create_user(self, app):
        from app import db
        user = User(
            name='John Doe',
            email='john@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.email == 'john@example.com'
    
    def test_password_hashing(self, test_user):
        assert not test_user.password_hash == 'password123'
        assert test_user.check_password('password123')
        assert not test_user.check_password('wrongpassword')
    
    def test_get_age(self, test_user):
        age = test_user.get_age()
        assert isinstance(age, int)
        assert age >= 23  # Test user was born in 2000


class TestMembership:
    def test_is_active(self, test_user):
        assert test_user.membership.is_active()
    
    def test_nights_remaining(self, test_user):
        from config.config import Config
        remaining = test_user.membership.nights_remaining()
        assert remaining == Config.MEMBERSHIP_NIGHTS_INCLUDED
    
    def test_renew(self, test_user):
        original_expiry = test_user.membership.expiry_date
        test_user.membership.renew()
        
        assert test_user.membership.start_date == date.today()
        assert test_user.membership.nights_used == 0
        assert test_user.membership.expiry_date > original_expiry


class TestCredit:
    def test_credit_balance(self, app):
        from app import db
        user = User(
            name='Test',
            email='test@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        credit = Credit(user_id=user.id, amount=10)
        db.session.add(credit)
        db.session.commit()
        
        assert credit.balance() == 10
        assert not credit.is_expired()
