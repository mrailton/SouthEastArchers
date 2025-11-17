"""Tests for credit model"""
import pytest
from app.models import User, Credit
from datetime import date


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

    def test_credit_balance_with_usage(self, app):
        """Test balance calculation with used credits"""
        from app import db
        user = User(
            name='Test',
            email='test@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        credit = Credit(user_id=user.id, amount=10, used=3)
        db.session.add(credit)
        db.session.commit()
        
        assert credit.balance() == 7

    def test_credit_zero_balance(self, app):
        """Test credit with zero balance"""
        from app import db
        user = User(
            name='Test',
            email='test@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        credit = Credit(user_id=user.id, amount=5, used=5)
        db.session.add(credit)
        db.session.commit()
        
        assert credit.balance() == 0
