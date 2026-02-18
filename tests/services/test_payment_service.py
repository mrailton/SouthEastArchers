"""Tests for payment service"""

from datetime import date
from unittest.mock import patch

from flask import session

from app import db
from app.models import Credit, Payment
from app.services import PaymentProcessingService, PaymentService
from tests.helpers import create_payment_for_user

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
        payment = create_payment_for_user(db, test_user, description="Renewal", status="pending")

        session["membership_renewal_payment_id"] = payment.id
        result = {"transaction_code": "txn_new_123"}

        with patch("app.services.payment_processing_service.PaymentProcessingService.send_payment_receipt"):
            PaymentProcessingService.handle_membership_renewal(test_user.id, "checkout_new", result)

        # Verify membership was created
        db.session.refresh(test_user)
        assert test_user.membership is not None
        assert test_user.membership.status == "active"
        # Expiry calculated based on membership year
        # Jan 25 is before March 1, so expires Feb 28, 2026
        assert test_user.membership.expiry_date.year == 2026
        assert test_user.membership.expiry_date > date.today()


def test_send_payment_receipt_synchronously(app, test_user):
    """Test sending receipt email synchronously"""
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        with patch("app.utils.email.send_payment_receipt") as mock_send:
            PaymentProcessingService.send_payment_receipt(test_user.id, payment.id)
            mock_send.assert_called_once()


def test_send_payment_receipt_with_exception(app, test_user):
    """Test receipt sending when email raises exception"""
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        with patch("app.utils.email.send_payment_receipt", side_effect=Exception("Email error")):
            # Should not raise, just log error
            PaymentProcessingService.send_payment_receipt(test_user.id, payment.id)


def test_handle_signup_payment_with_membership(app, test_user):
    """Test signup payment activation with membership"""
    # Give test_user a pending membership
    test_user.membership.status = "pending"
    db.session.commit()

    with app.test_request_context():
        payment = create_payment_for_user(db, test_user, status="pending")

        session["signup_payment_id"] = payment.id
        result = {"transaction_code": "txn_signup_123"}

        with patch("app.services.payment_processing_service.PaymentProcessingService.send_payment_receipt"):
            PaymentProcessingService.handle_signup_payment(test_user.id, "checkout_signup", result)

            # Verify membership was activated
            db.session.refresh(test_user)
            assert test_user.membership.status == "active"


@patch("app.services.mail_service.send_credit_purchase_receipt")
def test_handle_credit_purchase_with_quantity(mock_send_email, app, test_user):
    """Test credit purchase creates correct amount of credits and sends email"""
    with app.test_request_context():
        payment = create_payment_for_user(db, test_user, amount_cents=5000, payment_type="credits", status="pending")

        # User starts with 20 initial credits (from test_user fixture with membership)
        initial_total = test_user.membership.credits_remaining()
        quantity = 10
        session["credit_purchase_payment_id"] = payment.id
        session["credit_purchase_quantity"] = quantity
        result = {"transaction_id": "txn_credits_123"}

        PaymentProcessingService.handle_credit_purchase(test_user.id, "checkout_credits", result)

        # Verify credit record was created with correct quantity
        credit = Credit.query.filter_by(user_id=test_user.id, payment_id=payment.id).first()
        assert credit is not None
        assert credit.amount == quantity

        # Verify credits were added to membership (as purchased credits)
        db.session.refresh(test_user)
        assert test_user.membership.credits_remaining() == initial_total + quantity

        # Verify email was sent with correct parameters
        mock_send_email.assert_called_once_with(test_user.id, payment.id, quantity)


@patch("app.services.mail_service.send_credit_purchase_receipt")
def test_handle_credit_purchase_email_failure(mock_send_email, app, test_user):
    """Test credit purchase succeeds even if email fails"""
    # Make email sending fail
    mock_send_email.side_effect = Exception("Mail server down")

    with app.test_request_context():
        payment = create_payment_for_user(db, test_user, amount_cents=3000, payment_type="credits", status="pending")

        initial_total = test_user.membership.credits_remaining()
        quantity = 5
        session["credit_purchase_payment_id"] = payment.id
        session["credit_purchase_quantity"] = quantity
        result = {"transaction_id": "txn_456"}

        # Should not raise exception even though email fails
        response = PaymentProcessingService.handle_credit_purchase(test_user.id, "checkout_456", result)

        # Verify payment still completed successfully
        assert response is not None
        db.session.refresh(payment)
        assert payment.status == "completed"

        # Verify credits were still added
        db.session.refresh(test_user)
        assert test_user.membership.credits_remaining() == initial_total + quantity

        # Verify credit record was still created
        credit = Credit.query.filter_by(user_id=test_user.id, payment_id=payment.id).first()
        assert credit is not None
        assert credit.amount == quantity

        # Verify email was attempted
        mock_send_email.assert_called_once()


# Cash Payment Service Tests


@patch("app.services.mail_service.send_cash_payment_pending_email")
def test_initiate_cash_membership_payment_success(mock_send_email, app, test_user):
    """Test initiating cash membership payment creates pending payment"""
    service = PaymentService()
    result = service.initiate_cash_membership_payment(test_user)

    assert result["success"] is True
    assert "payment_id" in result
    assert result["amount"] == app.config["ANNUAL_MEMBERSHIP_COST"] / 100.0
    assert "instructions" in result

    # Verify payment record was created with correct attributes
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
    assert payment.amount_cents == app.config["ANNUAL_MEMBERSHIP_COST"]

    # Verify email was sent
    mock_send_email.assert_called_once_with(test_user.id, payment.id)


@patch("app.services.mail_service.send_cash_payment_pending_email")
def test_initiate_cash_credit_purchase_success(mock_send_email, app, test_user):
    """Test initiating cash credit purchase creates pending payment"""
    from app.services.settings_service import SettingsService

    service = PaymentService()
    quantity = 5
    result = service.initiate_cash_credit_purchase(test_user, quantity)

    settings = SettingsService.get()
    assert result["success"] is True
    assert "payment_id" in result
    assert result["quantity"] == quantity
    expected_amount = quantity * settings.additional_shoot_cost / 100.0
    assert result["amount"] == expected_amount
    assert "instructions" in result

    # Verify payment record was created with correct attributes
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_type="credits",
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
    assert payment.amount_cents == quantity * settings.additional_shoot_cost
    assert f"{quantity} shooting credits" in payment.description

    # Verify email was sent
    mock_send_email.assert_called_once_with(test_user.id, payment.id)


@patch("app.services.mail_service.send_cash_payment_pending_email")
def test_initiate_cash_credit_purchase_different_quantities(mock_send_email, app, test_user):
    """Test cash credit purchase with different quantities"""
    from app.services.settings_service import SettingsService

    service = PaymentService()
    settings = SettingsService.get()

    for quantity in [1, 5, 10, 20]:
        result = service.initiate_cash_credit_purchase(test_user, quantity)
        assert result["success"] is True
        assert result["quantity"] == quantity

        expected_amount = quantity * settings.additional_shoot_cost
        payment = (
            Payment.query.filter_by(
                user_id=test_user.id,
                payment_type="credits",
                payment_method="cash",
            )
            .order_by(Payment.id.desc())
            .first()
        )
        assert payment.amount_cents == expected_amount


@patch("app.services.mail_service.send_cash_payment_pending_email")
def test_initiate_cash_membership_email_failure_does_not_block(mock_send_email, app, test_user):
    """Test cash membership payment succeeds even if confirmation email fails"""
    mock_send_email.side_effect = Exception("Mail server down")

    service = PaymentService()
    result = service.initiate_cash_membership_payment(test_user)

    # Payment should still succeed even if email fails
    assert result["success"] is True
    assert "payment_id" in result

    # Verify payment was created
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
