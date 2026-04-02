"""Tests for payment service"""

from datetime import date
from unittest.mock import patch

from app import db
from app.models import Credit, Payment
from app.services import PaymentProcessingService, PaymentService
from app.services.settings_service import SettingsService
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


def test_initiate_membership_payment_success(app, test_user):
    """Test initiating membership payment successfully"""
    with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
        mock_checkout.return_value = {"id": "checkout_123"}

        service = PaymentService()
        result = service.initiate_membership_payment(test_user)

        assert result.success is True
        assert result.data["checkout_id"] == "checkout_123"
        assert result.data["user_id"] == test_user.id
        assert result.data["amount"] == SettingsService.get("annual_membership_cost") / 100.0
        payment = Payment.query.filter_by(user_id=test_user.id, payment_type="membership", status="pending").first()
        assert payment is not None


def test_initiate_membership_payment_checkout_fails(app, test_user):
    """Test membership payment when checkout creation fails"""
    with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
        mock_checkout.return_value = None

        initial_payment_count = Payment.query.count()

        service = PaymentService()
        result = service.initiate_membership_payment(test_user)

        assert result.success is False
        assert "Error creating payment" in result.message
        # Payment should be rolled back
        assert Payment.query.count() == initial_payment_count


def test_initiate_credit_purchase_success(app, test_user):
    """Test initiating credit purchase successfully"""
    with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
        mock_checkout.return_value = {"id": "checkout_456"}

        service = PaymentService()
        quantity = 5
        result = service.initiate_credit_purchase(test_user, quantity)

        assert result.success is True
        assert result.data["checkout_id"] == "checkout_456"
        assert result.data["user_id"] == test_user.id
        assert result.data["quantity"] == quantity

        expected_amount = quantity * SettingsService.get("additional_shoot_cost") / 100.0
        assert result.data["amount"] == expected_amount


def test_initiate_credit_purchase_checkout_fails(app, test_user):
    """Test credit purchase when checkout creation fails"""
    with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
        mock_checkout.return_value = None

        initial_payment_count = Payment.query.count()

        service = PaymentService()
        result = service.initiate_credit_purchase(test_user, 3)

        assert result.success is False
        assert "Error creating payment" in result.message
        # Payment should be rolled back
        assert Payment.query.count() == initial_payment_count


def test_initiate_credit_purchase_different_quantities(app, test_user):
    """Test credit purchase with different quantities"""
    with patch("app.services.payment_service.PaymentService.create_checkout") as mock_checkout:
        mock_checkout.return_value = {"id": "checkout_789"}

        service = PaymentService()

        for quantity in [1, 5, 10, 20]:
            result = service.initiate_credit_purchase(test_user, quantity)
            assert result.success is True

            expected_amount = quantity * SettingsService.get("additional_shoot_cost")
            payment = Payment.query.filter_by(user_id=test_user.id, payment_type="credits").order_by(Payment.id.desc()).first()
            assert payment.amount_cents == expected_amount


# TestPaymentProcessingService — pure business logic (no Flask session/request context needed)


def test_handle_signup_payment_not_found(app):
    """Test handle_signup_payment when payment not found"""
    result = PaymentProcessingService.handle_signup_payment(user_id=1, payment_id=99999, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_signup_payment_user_not_found(app, test_user):
    """Test handle_signup_payment when user not found"""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = PaymentProcessingService.handle_signup_payment(user_id=99999, payment_id=payment.id, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_signup_payment_activates_membership(app, test_user):
    """Test signup payment activation with membership"""
    test_user.membership.status = "pending"
    db.session.commit()

    payment = create_payment_for_user(db, test_user, status="pending")
    result = PaymentProcessingService.handle_signup_payment(test_user.id, payment.id, "txn_signup_123")

    assert result.success is True
    db.session.refresh(test_user)
    assert test_user.membership.status == "active"
    db.session.refresh(payment)
    assert payment.status == "completed"
    assert payment.external_transaction_id == "txn_signup_123"


def test_handle_membership_renewal_not_found(app):
    """Test handle_membership_renewal when payment not found"""
    result = PaymentProcessingService.handle_membership_renewal(user_id=1, payment_id=99999, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_membership_renewal_user_not_found(app, test_user):
    """Test handle_membership_renewal when user not found"""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = PaymentProcessingService.handle_membership_renewal(user_id=99999, payment_id=payment.id, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_membership_renewal_renews_existing(app, test_user):
    """Test membership renewal renews existing membership"""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = PaymentProcessingService.handle_membership_renewal(test_user.id, payment.id, "txn_renew_123")

    assert result.success is True
    db.session.refresh(test_user)
    assert test_user.membership.status == "active"
    db.session.refresh(payment)
    assert payment.status == "completed"


def test_handle_membership_renewal_creates_membership_if_missing(app, test_user):
    """Test membership renewal creates membership if user doesn't have one"""
    if test_user.membership:
        db.session.delete(test_user.membership)
        db.session.commit()

    payment = create_payment_for_user(db, test_user, description="Renewal", status="pending")
    result = PaymentProcessingService.handle_membership_renewal(test_user.id, payment.id, "txn_new_123")

    assert result.success is True
    db.session.refresh(test_user)
    assert test_user.membership is not None
    assert test_user.membership.status == "active"
    expected_expiry = SettingsService.calculate_membership_expiry(date.today()).date()
    assert test_user.membership.expiry_date == expected_expiry


def test_handle_credit_purchase_not_found(app):
    """Test handle_credit_purchase when payment not found"""
    result = PaymentProcessingService.handle_credit_purchase(user_id=1, payment_id=99999, quantity=5, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_credit_purchase_user_not_found(app, test_user):
    """Test handle_credit_purchase when user not found"""
    payment = create_payment_for_user(db, test_user, amount_cents=5000, payment_type="credits", status="pending")
    result = PaymentProcessingService.handle_credit_purchase(user_id=99999, payment_id=payment.id, quantity=5, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


@patch("app.services.mail_service.MailService.send_credit_purchase_receipt")
def test_handle_credit_purchase_with_quantity(mock_send_email, app, test_user):
    """Test credit purchase creates correct amount of credits and sends email via event"""
    payment = create_payment_for_user(db, test_user, amount_cents=5000, payment_type="credits", status="pending")

    initial_total = test_user.membership.credits_remaining()
    quantity = 10

    result = PaymentProcessingService.handle_credit_purchase(test_user.id, payment.id, quantity, "txn_credits_123")

    assert result.success is True
    assert "10 credits" in result.message

    # Verify credit record was created with correct quantity
    credit = Credit.query.filter_by(user_id=test_user.id, payment_id=payment.id).first()
    assert credit is not None
    assert credit.amount == quantity

    # Verify credits were added to membership (as purchased credits)
    db.session.refresh(test_user)
    assert test_user.membership.credits_remaining() == initial_total + quantity

    # Verify email was sent via domain event
    mock_send_email.assert_called_once_with(test_user.id, payment.id, quantity)


@patch("app.services.mail_service.MailService.send_credit_purchase_receipt")
def test_handle_credit_purchase_email_failure(mock_send_email, app, test_user):
    """Test credit purchase succeeds even if email fails"""
    mock_send_email.side_effect = Exception("Mail server down")

    payment = create_payment_for_user(db, test_user, amount_cents=3000, payment_type="credits", status="pending")
    initial_total = test_user.membership.credits_remaining()
    quantity = 5

    result = PaymentProcessingService.handle_credit_purchase(test_user.id, payment.id, quantity, "txn_456")

    # Service should still succeed
    assert result.success is True

    # Verify payment completed
    db.session.refresh(payment)
    assert payment.status == "completed"

    # Verify credits were still added
    db.session.refresh(test_user)
    assert test_user.membership.credits_remaining() == initial_total + quantity

    # Verify credit record was still created
    credit = Credit.query.filter_by(user_id=test_user.id, payment_id=payment.id).first()
    assert credit is not None
    assert credit.amount == quantity

    # Verify email was attempted via event
    mock_send_email.assert_called_once()


# Cash Payment Service Tests


@patch("app.services.mail_service.MailService.send_cash_payment_pending_email")
def test_initiate_cash_membership_payment_success(mock_send_email, app, test_user):
    """Test initiating cash membership payment creates pending payment"""
    service = PaymentService()
    result = service.initiate_cash_membership_payment(test_user)

    assert result.success is True
    assert "payment_id" in result.data
    assert result.data["amount"] == SettingsService.get("annual_membership_cost") / 100.0
    assert "instructions" in result.data

    # Verify payment record was created with correct attributes
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
    assert payment.amount_cents == SettingsService.get("annual_membership_cost")

    # Verify email was sent
    mock_send_email.assert_called_once_with(test_user.id, payment.id)


@patch("app.services.mail_service.MailService.send_cash_payment_pending_email")
def test_initiate_cash_credit_purchase_success(mock_send_email, app, test_user):
    """Test initiating cash credit purchase creates pending payment"""
    service = PaymentService()
    quantity = 5
    result = service.initiate_cash_credit_purchase(test_user, quantity)

    additional_shoot_cost = SettingsService.get("additional_shoot_cost")
    assert result.success is True
    assert "payment_id" in result.data
    assert result.data["quantity"] == quantity
    expected_amount = quantity * additional_shoot_cost / 100.0
    assert result.data["amount"] == expected_amount
    assert "instructions" in result.data

    # Verify payment record was created with correct attributes
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_type="credits",
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
    assert payment.amount_cents == quantity * additional_shoot_cost
    assert f"{quantity} shooting credits" in payment.description

    # Verify email was sent
    mock_send_email.assert_called_once_with(test_user.id, payment.id)


@patch("app.services.mail_service.MailService.send_cash_payment_pending_email")
def test_initiate_cash_credit_purchase_different_quantities(mock_send_email, app, test_user):
    """Test cash credit purchase with different quantities"""
    service = PaymentService()
    additional_shoot_cost = SettingsService.get("additional_shoot_cost")

    for quantity in [1, 5, 10, 20]:
        result = service.initiate_cash_credit_purchase(test_user, quantity)
        assert result.success is True
        assert result.data["quantity"] == quantity

        expected_amount = quantity * additional_shoot_cost
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


@patch("app.services.mail_service.MailService.send_cash_payment_pending_email")
def test_initiate_cash_membership_email_failure_does_not_block(mock_send_email, app, test_user):
    """Test cash membership payment succeeds even if confirmation email fails"""
    mock_send_email.side_effect = Exception("Mail server down")

    service = PaymentService()
    result = service.initiate_cash_membership_payment(test_user)

    # Payment should still succeed even if email fails
    assert result.success is True
    assert "payment_id" in result.data

    # Verify payment was created
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
