"""Tests for credit model"""
import pytest
from app.models import User, Credit
from datetime import date


class TestCredit:
    def test_create_credit(self, app):
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
        
        assert credit.id is not None
        assert credit.amount == 10
        assert credit.user_id == user.id

    def test_credit_with_payment(self, app):
        """Test credit linked to payment"""
        from app import db
        from app.models import Payment
        
        user = User(
            name='Test',
            email='test@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        payment = Payment(
            user_id=user.id,
            amount=25.0,
            currency='EUR',
            payment_type='credits',
            status='completed'
        )
        db.session.add(payment)
        db.session.flush()
        
        credit = Credit(user_id=user.id, amount=5, payment_id=payment.id)
        db.session.add(credit)
        db.session.commit()
        
        assert credit.payment_id == payment.id
