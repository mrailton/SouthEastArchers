"""Tests for payment service"""

import pytest
from flask import session

from app.services.payment_service import PaymentProcessingService


class TestPaymentProcessingService:
    """Test PaymentProcessingService methods"""

    def test_validate_card_details_all_present(self):
        """Test validation with all details present"""
        assert PaymentProcessingService.validate_card_details(
            "1234567890123456", "John Doe", "12", "2025", "123"
        )

    def test_validate_card_details_missing_fields(self):
        """Test validation with missing fields"""
        assert not PaymentProcessingService.validate_card_details(
            "", "John Doe", "12", "2025", "123"
        )
        assert not PaymentProcessingService.validate_card_details(
            "1234567890123456", "", "12", "2025", "123"
        )
        assert not PaymentProcessingService.validate_card_details(
            "1234567890123456", "John Doe", "", "2025", "123"
        )

    def test_handle_signup_payment_no_payment_found(self, app):
        """Test handle_signup_payment when payment not found"""
        with app.test_request_context():
            session["signup_payment_id"] = 99999
            result = {"transaction_id": "test_123", "success": True}
            response = PaymentProcessingService.handle_signup_payment(
                user_id=1, checkout_id="checkout_123", result=result
            )
            assert response is None

    def test_handle_signup_payment_no_user_found(self, app):
        """Test handle_signup_payment when user not found"""
        from app import db
        from app.models import Payment

        with app.test_request_context():
            payment = Payment(
                user_id=99999,
                amount=100.0,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                description="Test",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()

            session["signup_payment_id"] = payment.id
            result = {"transaction_id": "test_123", "success": True}
            response = PaymentProcessingService.handle_signup_payment(
                user_id=99999, checkout_id="checkout_123", result=result
            )
            assert response is None

    def test_handle_membership_renewal_no_payment_found(self, app):
        """Test handle_membership_renewal when payment not found"""
        with app.test_request_context():
            session["membership_renewal_payment_id"] = 99999
            result = {"transaction_id": "test_123", "success": True}
            response = PaymentProcessingService.handle_membership_renewal(
                user_id=1, checkout_id="checkout_123", result=result
            )
            assert response is None

    def test_handle_membership_renewal_no_user_found(self, app):
        """Test handle_membership_renewal when user not found"""
        from app import db
        from app.models import Payment

        with app.test_request_context():
            payment = Payment(
                user_id=99999,
                amount=100.0,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                description="Test",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()

            session["membership_renewal_payment_id"] = payment.id
            result = {"transaction_id": "test_123", "success": True}
            response = PaymentProcessingService.handle_membership_renewal(
                user_id=99999, checkout_id="checkout_123", result=result
            )
            assert response is None

    def test_handle_credit_purchase_no_payment_found(self, app):
        """Test handle_credit_purchase when payment not found"""
        with app.test_request_context():
            session["credit_purchase_payment_id"] = 99999
            result = {"transaction_id": "test_123", "success": True}
            response = PaymentProcessingService.handle_credit_purchase(
                user_id=1, checkout_id="checkout_123", result=result
            )
            assert response is None

    def test_handle_credit_purchase_no_user_found(self, app):
        """Test handle_credit_purchase when user not found"""
        from app import db
        from app.models import Payment

        with app.test_request_context():
            payment = Payment(
                user_id=99999,
                amount=50.0,
                currency="EUR",
                payment_type="credits",
                payment_method="online",
                description="Test",
                status="pending",
            )
            db.session.add(payment)
            db.session.commit()

            session["credit_purchase_payment_id"] = payment.id
            result = {"transaction_id": "test_123", "success": True}
            response = PaymentProcessingService.handle_credit_purchase(
                user_id=99999, checkout_id="checkout_123", result=result
            )
            assert response is None
