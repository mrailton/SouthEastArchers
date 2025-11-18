"""Tests for payment model"""
import pytest
from app.models import User, Payment
from datetime import date


class TestPayment:
    def test_create_payment(self, app, test_user):
        from app import db
        payment = Payment(
            user_id=test_user.id,
            amount=50.0,
            currency='GBP',
            payment_type='membership',
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()
        
        assert payment.id is not None
        assert payment.amount == 50.0
        assert payment.status == 'completed'
