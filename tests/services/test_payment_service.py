"""Tests for payment service"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from flask import session

from app import db
from app.models import Credit, Membership, Payment, User
from app.services.payment_service import PaymentProcessingService, PaymentService

# TestPaymentService module-level functions


def test_create_checkout_success(app, test_user):
    """Test creating a checkout successfully"""
    with patch("app.services.sumup_service.SumUpService.create_checkout") as mock_checkout:
        mock_checkout.return_value = {"id": "checkout_123", "status": "PENDING"}

        service = PaymentService()
        result = service.create_checkout(10000, "Test payment")

        assert result is not None
        assert result["id"] == "checkout_123"
        mock_checkout.assert_called_once()


def test_create_checkout_failure(app, test_user):
    """Test creating checkout when API fails"""
    with patch("app.services.sumup_service.SumUpService.create_checkout") as mock_checkout:
        mock_checkout.return_value = None

        service = PaymentService()
        result = service.create_checkout(10000, "Test payment")

        assert result is None


def test_process_payment_success(app):
    """Test processing payment successfully"""
    with patch("app.services.sumup_service.SumUpService.process_checkout_payment") as mock_process:
        mock_process.return_value = {"status": "PAID", "transaction_id": "txn_123"}

        service = PaymentService()
        result = service.process_payment("checkout_123", "4111111111111111", "John Doe", "12", "2025", "123")

        assert result is not None
        assert result["status"] == "PAID"


def test_initiate_membership_payment_success(app, test_user):
    """Test initiating membership payment successfully"""
    with app.test_request_context():
        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = {"id": "checkout_123"}

            service = PaymentService()
            result = service.initiate_membership_payment(test_user)

            assert result["success"] is True
            assert result["checkout_id"] == "checkout_123"
            assert session.get("membership_renewal_user_id") == test_user.id
            assert session.get("checkout_amount") == app.config["ANNUAL_MEMBERSHIP_COST"] / 100.0

            # Verify payment record was created
            payment = Payment.query.filter_by(user_id=test_user.id, payment_type="membership", status="pending").first()
            assert payment is not None


def test_initiate_membership_payment_checkout_fails(app, test_user):
    """Test membership payment when checkout creation fails"""
    with app.test_request_context():
        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = None

            initial_payment_count = Payment.query.count()

            service = PaymentService()
            result = service.initiate_membership_payment(test_user)

            assert result["success"] is False
            assert "error" in result
            # Payment should be rolled back
            assert Payment.query.count() == initial_payment_count


def test_initiate_credit_purchase_success(app, test_user):
    """Test initiating credit purchase successfully"""
    with app.test_request_context():
        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = {"id": "checkout_456"}

            service = PaymentService()
            quantity = 5
            result = service.initiate_credit_purchase(test_user, quantity)

            assert result["success"] is True
            assert result["checkout_id"] == "checkout_456"
            assert session.get("credit_purchase_user_id") == test_user.id
            assert session.get("credit_purchase_quantity") == quantity

            expected_amount = quantity * app.config["ADDITIONAL_NIGHT_COST"] / 100.0
            assert session.get("checkout_amount") == expected_amount


def test_initiate_credit_purchase_checkout_fails(app, test_user):
    """Test credit purchase when checkout creation fails"""
    with app.test_request_context():
        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = None

            initial_payment_count = Payment.query.count()

            service = PaymentService()
            result = service.initiate_credit_purchase(test_user, 3)

            assert result["success"] is False
            assert "error" in result
            # Payment should be rolled back
            assert Payment.query.count() == initial_payment_count


def test_initiate_credit_purchase_different_quantities(app, test_user):
    """Test credit purchase with different quantities"""
    with app.test_request_context():
        with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
            mock_checkout.return_value = {"id": "checkout_789"}

            service = PaymentService()

            for quantity in [1, 5, 10, 20]:
                result = service.initiate_credit_purchase(test_user, quantity)
                assert result["success"] is True

                expected_amount = quantity * app.config["ADDITIONAL_NIGHT_COST"]
                payment = Payment.query.filter_by(user_id=test_user.id, payment_type="credits").order_by(Payment.id.desc()).first()
                assert payment.amount_cents == expected_amount


# TestPaymentProcessingService module-level functions


def test_validate_card_details_all_present():
    """Test validation with all details present"""
    assert PaymentProcessingService.validate_card_details("1234567890123456", "John Doe", "12", "2025", "123")


def test_validate_card_details_missing_fields():
    """Test validation with missing fields"""
    assert not PaymentProcessingService.validate_card_details("", "John Doe", "12", "2025", "123")
    assert not PaymentProcessingService.validate_card_details("1234567890123456", "", "12", "2025", "123")
    assert not PaymentProcessingService.validate_card_details("1234567890123456", "John Doe", "", "2025", "123")


def test_handle_signup_payment_no_payment_found(app):
    """Test handle_signup_payment when payment not found"""
    with app.test_request_context():
        session["signup_payment_id"] = 99999
        result = {"transaction_id": "test_123", "success": True}
        response = PaymentProcessingService.handle_signup_payment(user_id=1, checkout_id="checkout_123", result=result)
        assert response is None


def test_handle_signup_payment_no_user_found(app):
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
        response = PaymentProcessingService.handle_signup_payment(user_id=99999, checkout_id="checkout_123", result=result)
        assert response is None


def test_handle_membership_renewal_no_payment_found(app):
    """Test handle_membership_renewal when payment not found"""
    with app.test_request_context():
        session["membership_renewal_payment_id"] = 99999
        result = {"transaction_id": "test_123", "success": True}
        response = PaymentProcessingService.handle_membership_renewal(user_id=1, checkout_id="checkout_123", result=result)
        assert response is None


def test_handle_membership_renewal_no_user_found(app):
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
        response = PaymentProcessingService.handle_membership_renewal(user_id=99999, checkout_id="checkout_123", result=result)
        assert response is None


def test_handle_credit_purchase_no_payment_found(app):
    """Test handle_credit_purchase when payment not found"""
    with app.test_request_context():
        session["credit_purchase_payment_id"] = 99999
        result = {"transaction_id": "test_123", "success": True}
        response = PaymentProcessingService.handle_credit_purchase(user_id=1, checkout_id="checkout_123", result=result)
        assert response is None


def test_handle_credit_purchase_no_user_found(app):
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
        response = PaymentProcessingService.handle_credit_purchase(user_id=99999, checkout_id="checkout_123", result=result)
        assert response is None


def test_handle_payment_failure_failed_status(app):
    """Test handling failed payment"""
    with app.test_request_context():
        result = {"status": "FAILED", "error": "Card declined"}
        response = PaymentProcessingService.handle_payment_failure("checkout_123", result)

        # Should redirect to checkout page
        assert response.status_code == 302
        assert "/payment/checkout/checkout_123" in response.location


def test_handle_payment_failure_pending_status(app):
    """Test handling pending payment"""
    with app.test_request_context():
        result = {"status": "PENDING", "error": "Payment processing"}
        response = PaymentProcessingService.handle_payment_failure("checkout_456", result)

        assert response.status_code == 302
        assert "/payment/checkout/checkout_456" in response.location


def test_handle_payment_failure_unknown_status(app):
    """Test handling unknown payment status"""
    with app.test_request_context():
        result = {"status": "UNKNOWN", "error": "Something went wrong"}
        response = PaymentProcessingService.handle_payment_failure("checkout_789", result)

        assert response.status_code == 302


def test_handle_membership_renewal_creates_membership_if_missing(app, test_user):
    """Test membership renewal creates membership if user doesn't have one"""
    # Remove existing membership
    if test_user.membership:
        db.session.delete(test_user.membership)
        db.session.commit()

    with app.test_request_context():
        payment = Payment(
            user_id=test_user.id,
            amount_cents=10000,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            description="Renewal",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        session["membership_renewal_payment_id"] = payment.id
        result = {"transaction_code": "txn_new_123"}

        with patch("app.services.payment_service.PaymentProcessingService.send_payment_receipt"):
            PaymentProcessingService.handle_membership_renewal(test_user.id, "checkout_new", result)

        # Verify membership was created
        db.session.refresh(test_user)
        assert test_user.membership is not None
        assert test_user.membership.status == "active"
        assert test_user.membership.expiry_date == date.today() + timedelta(days=365)


def test_queue_payment_receipt_with_task_queue(app, test_user):
    """Test queueing receipt with task queue available"""
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with app.test_request_context():
        with patch("app.services.payment_service.task_queue") as mock_queue:
            from unittest.mock import MagicMock

            mock_queue.enqueue = MagicMock()

            PaymentProcessingService.send_payment_receipt(test_user.id, payment.id)

            mock_queue.enqueue.assert_called_once()


def test_queue_payment_receipt_task_queue_exception(app, test_user):
    """Test queueing receipt when task queue raises exception"""
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with app.test_request_context():
        with patch("app.services.payment_service.task_queue") as mock_queue:
            mock_queue.enqueue.side_effect = Exception("Queue error")

            # Should not raise, just log error
            PaymentProcessingService.send_payment_receipt(test_user.id, payment.id)


def test_queue_payment_receipt_fallback_to_direct_send(app, test_user):
    """Test receipt fallback to direct send when no task queue"""
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with app.test_request_context():
        with patch("app.services.payment_service.task_queue", None):
            with patch("app.utils.email.send_payment_receipt") as mock_send:
                PaymentProcessingService.send_payment_receipt(test_user.id, payment.id)
                mock_send.assert_called_once()


def test_queue_payment_receipt_fallback_send_exception(app, test_user):
    """Test receipt fallback when direct send raises exception"""
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with app.test_request_context():
        with patch("app.services.payment_service.task_queue", None):
            with patch("app.utils.email.send_payment_receipt", side_effect=Exception("Email error")):
                # Should not raise, just log error
                PaymentProcessingService.send_payment_receipt(test_user.id, payment.id)


def test_handle_signup_payment_with_membership(app, test_user):
    """Test signup payment activation with membership"""
    # Give test_user a pending membership
    test_user.membership.status = "pending"
    db.session.commit()

    with app.test_request_context():
        payment = Payment(
            user_id=test_user.id,
            amount_cents=10000,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        session["signup_payment_id"] = payment.id
        result = {"transaction_code": "txn_signup_123"}

        with patch("app.services.payment_service.PaymentProcessingService.send_payment_receipt"):
            PaymentProcessingService.handle_signup_payment(test_user.id, "checkout_signup", result)

            # Verify membership was activated
            db.session.refresh(test_user)
            assert test_user.membership.status == "active"


def test_handle_credit_purchase_with_quantity(app, test_user):
    """Test credit purchase creates correct amount of credits"""
    with app.test_request_context():
        payment = Payment(
            user_id=test_user.id,
            amount_cents=5000,
            currency="EUR",
            payment_type="credits",
            payment_method="online",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        quantity = 10
        session["credit_purchase_payment_id"] = payment.id
        session["credit_purchase_quantity"] = quantity
        result = {"transaction_id": "txn_credits_123"}

        PaymentProcessingService.handle_credit_purchase(test_user.id, "checkout_credits", result)

        # Verify credit record was created with correct quantity
        credit = Credit.query.filter_by(user_id=test_user.id, payment_id=payment.id).first()
        assert credit is not None
        assert credit.amount == quantity
