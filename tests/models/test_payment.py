"""Tests for payment model"""

from datetime import date

import pytest

from app.models import Payment, User


class TestPayment:
    def test_create_payment(self, app, test_user):
        from app import db

        payment = Payment(
            user_id=test_user.id,
            amount=50.0,
            currency="GBP",
            payment_type="membership",
            status="completed",
        )
        db.session.add(payment)
        db.session.commit()

        assert payment.id is not None
        assert payment.amount == 50.0
        assert payment.status == "completed"

    def test_mark_completed(self, app, test_user):
        """Test marking payment as completed"""
        from app import db

        payment = Payment(
            user_id=test_user.id,
            amount=50.0,
            currency="GBP",
            payment_type="membership",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        payment.mark_completed("txn_123")
        assert payment.status == "completed"
        assert payment.sumup_transaction_id == "txn_123"

    def test_mark_failed(self, app, test_user):
        """Test marking payment as failed"""
        from app import db

        payment = Payment(
            user_id=test_user.id,
            amount=50.0,
            currency="GBP",
            payment_type="membership",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        payment.mark_failed()
        assert payment.status == "failed"

    def test_payment_repr(self, app, test_user):
        """Test payment string representation"""
        from app import db

        payment = Payment(
            user_id=test_user.id,
            amount=50.0,
            currency="GBP",
            payment_type="membership",
            status="completed",
        )
        db.session.add(payment)
        db.session.commit()

        repr_str = repr(payment)
        assert "Payment" in repr_str
        assert str(test_user.id) in repr_str
        assert "completed" in repr_str
