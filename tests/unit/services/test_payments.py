from datetime import date
from unittest.mock import patch

from app import db
from app.models import Credit, Payment
from app.services import payment_processing, payments, settings
from tests.helpers import FakePaymentProcessor, create_payment_for_user

# TestPaymentService module-level functions


def test_initiate_membership_payment_success(app, test_user):
    """Test initiating membership payment successfully"""
    processor = FakePaymentProcessor(checkout_response={"id": "checkout_123"})
    result = payments.initiate_membership_payment(test_user, processor=processor)

    assert result.success is True
    assert result.data["checkout_id"] == "checkout_123"
    assert result.data["user_id"] == test_user.id
    assert result.data["amount"] == settings.get("annual_membership_cost") / 100.0
    payment = Payment.query.filter_by(user_id=test_user.id, payment_type="membership", status="pending").first()
    assert payment is not None
    assert payment.sumup_checkout_id == "checkout_123"


def test_initiate_membership_payment_checkout_fails(app, test_user):
    """Test membership payment when checkout creation fails"""
    processor = FakePaymentProcessor(checkout_response=None)
    initial_payment_count = Payment.query.count()

    result = payments.initiate_membership_payment(test_user, processor=processor)

    assert result.success is False
    assert "Error creating payment" in result.message
    # Payment should be rolled back
    assert Payment.query.count() == initial_payment_count


def test_initiate_membership_payment_db_failure(app, test_user):
    """DB write failure after successful checkout creation returns an error without leaving a dangling SumUp checkout."""
    processor = FakePaymentProcessor(checkout_response={"id": "checkout_db_fail"})
    with patch("app.repositories.PaymentRepository.add", side_effect=Exception("DB error")):
        result = payments.initiate_membership_payment(test_user, processor=processor)
    assert result.success is False
    assert "Error creating payment" in result.message


def test_initiate_credit_purchase_db_failure(app, test_user):
    """DB write failure after successful credit checkout creation returns an error."""
    processor = FakePaymentProcessor(checkout_response={"id": "checkout_credit_db_fail"})
    with patch("app.repositories.PaymentRepository.add", side_effect=Exception("DB error")):
        result = payments.initiate_credit_purchase(test_user, 3, processor=processor)
    assert result.success is False
    assert "Error creating payment" in result.message


def test_initiate_credit_purchase_success(app, test_user):
    """Test initiating credit purchase successfully"""
    processor = FakePaymentProcessor(checkout_response={"id": "checkout_456"})
    quantity = 5
    result = payments.initiate_credit_purchase(test_user, quantity, processor=processor)

    assert result.success is True
    assert result.data["checkout_id"] == "checkout_456"
    assert result.data["user_id"] == test_user.id
    assert result.data["quantity"] == quantity

    expected_amount = quantity * settings.get("additional_shoot_cost") / 100.0
    assert result.data["amount"] == expected_amount


def test_initiate_credit_purchase_checkout_fails(app, test_user):
    """Test credit purchase when checkout creation fails"""
    processor = FakePaymentProcessor(checkout_response=None)
    initial_payment_count = Payment.query.count()

    result = payments.initiate_credit_purchase(test_user, 3, processor=processor)

    assert result.success is False
    assert "Error creating payment" in result.message
    # Payment should be rolled back
    assert Payment.query.count() == initial_payment_count


def test_initiate_credit_purchase_different_quantities(app, test_user):
    """Test credit purchase with different quantities"""
    processor = FakePaymentProcessor(checkout_response={"id": "checkout_789"})
    for quantity in [1, 5, 10, 20]:
        result = payments.initiate_credit_purchase(test_user, quantity, processor=processor)
        assert result.success is True

        expected_amount = quantity * settings.get("additional_shoot_cost")
        payment = Payment.query.filter_by(user_id=test_user.id, payment_type="credits").order_by(Payment.id.desc()).first()
        assert payment.amount_cents == expected_amount


# TestPaymentProcessingService — pure business logic (no Flask session/request context needed)


def test_handle_signup_payment_not_found(app):
    """Test handle_signup_payment when payment not found"""
    result = payment_processing.handle_signup_payment(user_id=1, payment_id=99999, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_signup_payment_user_not_found(app, test_user):
    """Test handle_signup_payment when user not found"""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = payment_processing.handle_signup_payment(user_id=99999, payment_id=payment.id, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_signup_payment_activates_membership(app, test_user):
    """Test signup payment activation with membership"""
    test_user.membership.status = "pending"
    db.session.commit()

    payment = create_payment_for_user(db, test_user, status="pending")
    result = payment_processing.handle_signup_payment(test_user.id, payment.id, "txn_signup_123")

    assert result.success is True
    db.session.refresh(test_user)
    assert test_user.membership.status == "active"
    db.session.refresh(payment)
    assert payment.status == "completed"
    assert payment.external_transaction_id == "txn_signup_123"


def test_handle_membership_renewal_not_found(app):
    """Test handle_membership_renewal when payment not found"""
    result = payment_processing.handle_membership_renewal(user_id=1, payment_id=99999, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_membership_renewal_user_not_found(app, test_user):
    """Test handle_membership_renewal when user not found"""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = payment_processing.handle_membership_renewal(user_id=99999, payment_id=payment.id, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_membership_renewal_renews_existing(app, test_user):
    """Test membership renewal renews existing membership"""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = payment_processing.handle_membership_renewal(test_user.id, payment.id, "txn_renew_123")

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
    result = payment_processing.handle_membership_renewal(test_user.id, payment.id, "txn_new_123")

    assert result.success is True
    db.session.refresh(test_user)
    assert test_user.membership is not None
    assert test_user.membership.status == "active"
    expected_expiry = settings.calculate_membership_expiry(date.today()).date()
    assert test_user.membership.expiry_date == expected_expiry


def test_handle_credit_purchase_not_found(app):
    """Test handle_credit_purchase when payment not found"""
    result = payment_processing.handle_credit_purchase(user_id=1, payment_id=99999, quantity=5, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


def test_handle_credit_purchase_user_not_found(app, test_user):
    """Test handle_credit_purchase when user not found"""
    payment = create_payment_for_user(db, test_user, amount_cents=5000, payment_type="credits", status="pending")
    result = payment_processing.handle_credit_purchase(user_id=99999, payment_id=payment.id, quantity=5, transaction_id="txn_123")
    assert result.success is False
    assert "not found" in result.message.lower()


@patch("app.services.mail.send_credit_purchase_receipt")
def test_handle_credit_purchase_with_quantity(mock_send_email, app, test_user):
    """Test credit purchase creates correct amount of credits and sends email via event"""
    payment = create_payment_for_user(db, test_user, amount_cents=5000, payment_type="credits", status="pending")

    initial_total = test_user.membership.credits_remaining()
    quantity = 10

    result = payment_processing.handle_credit_purchase(test_user.id, payment.id, quantity, "txn_credits_123")
    from app.events.background import flush_deferred_handlers

    flush_deferred_handlers()

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


@patch("app.services.mail.send_credit_purchase_receipt")
def test_handle_credit_purchase_email_failure(mock_send_email, app, test_user):
    """Test credit purchase succeeds even if email fails"""
    mock_send_email.side_effect = Exception("Mail server down")

    payment = create_payment_for_user(db, test_user, amount_cents=3000, payment_type="credits", status="pending")
    initial_total = test_user.membership.credits_remaining()
    quantity = 5

    result = payment_processing.handle_credit_purchase(test_user.id, payment.id, quantity, "txn_456")
    from app.events.background import flush_deferred_handlers

    flush_deferred_handlers()

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


# Commit-failure handling


@patch("app.repositories.base.BaseRepository.save", side_effect=Exception("DB write failed"))
def test_handle_signup_payment_commit_failure_returns_fail(mock_save, app, test_user):
    """If the commit fails, the service returns a failure result instead of propagating the exception."""
    test_user.membership.status = "pending"
    db.session.commit()

    payment = create_payment_for_user(db, test_user, status="pending")
    result = payment_processing.handle_signup_payment(test_user.id, payment.id, "txn_fail")

    assert result.success is False
    assert "could not be processed" in result.message


@patch("app.repositories.base.BaseRepository.save", side_effect=Exception("DB write failed"))
def test_handle_membership_renewal_commit_failure_returns_fail(mock_save, app, test_user):
    """If the commit fails, the service returns a failure result instead of propagating the exception."""
    payment = create_payment_for_user(db, test_user, status="pending")
    result = payment_processing.handle_membership_renewal(test_user.id, payment.id, "txn_fail")

    assert result.success is False
    assert "could not be processed" in result.message


@patch("app.repositories.base.BaseRepository.save", side_effect=Exception("DB write failed"))
def test_handle_credit_purchase_commit_failure_returns_fail(mock_save, app, test_user):
    """If the commit fails, the service returns a failure result instead of propagating the exception."""
    payment = create_payment_for_user(db, test_user, amount_cents=5000, payment_type="credits", status="pending")
    result = payment_processing.handle_credit_purchase(test_user.id, payment.id, 5, "txn_fail")

    assert result.success is False
    assert "could not be processed" in result.message


# Cash Payment Service Tests


@patch("app.services.mail.send_cash_payment_pending_email")
def test_initiate_cash_membership_payment_success(mock_send_email, app, test_user):
    """Test initiating cash membership payment creates pending payment"""
    result = payments.initiate_cash_membership_payment(test_user)

    assert result.success is True
    assert "payment_id" in result.data
    assert result.data["amount"] == settings.get("annual_membership_cost") / 100.0
    assert "instructions" in result.data

    # Verify payment record was created with correct attributes
    payment = Payment.query.filter_by(
        user_id=test_user.id,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    ).first()
    assert payment is not None
    assert payment.amount_cents == settings.get("annual_membership_cost")

    from app.events.background import flush_deferred_handlers

    flush_deferred_handlers()
    mock_send_email.assert_called_once_with(test_user.id, payment.id)


@patch("app.services.mail.send_cash_payment_pending_email")
def test_initiate_cash_credit_purchase_success(mock_send_email, app, test_user):
    """Test initiating cash credit purchase creates pending payment"""
    quantity = 5
    result = payments.initiate_cash_credit_purchase(test_user, quantity)

    additional_shoot_cost = settings.get("additional_shoot_cost")
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

    from app.events.background import flush_deferred_handlers

    flush_deferred_handlers()
    mock_send_email.assert_called_once_with(test_user.id, payment.id)


@patch("app.services.mail.send_cash_payment_pending_email")
def test_initiate_cash_credit_purchase_different_quantities(mock_send_email, app, test_user):
    """Test cash credit purchase with different quantities"""
    additional_shoot_cost = settings.get("additional_shoot_cost")

    for quantity in [1, 5, 10, 20]:
        result = payments.initiate_cash_credit_purchase(test_user, quantity)
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


@patch("app.services.mail.send_cash_payment_pending_email")
def test_initiate_cash_membership_email_failure_does_not_block(mock_send_email, app, test_user):
    """Test cash membership payment succeeds even if confirmation email fails"""
    mock_send_email.side_effect = Exception("Mail server down")

    result = payments.initiate_cash_membership_payment(test_user)

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


def test_validate_credit_quantity_invalid(app):
    result = payments.validate_credit_quantity(0)
    assert result.success is False
    result = payments.validate_credit_quantity(51)
    assert result.success is False


def test_get_user_payments(app, test_user):
    create_payment_for_user(db, test_user, payment_type="membership", status="completed")
    rows = payments.get_user_payments(test_user.id)
    assert len(rows) >= 1


def test_get_completed_membership_payment(app, test_user):
    create_payment_for_user(db, test_user, payment_type="membership", status="completed")
    payment = payments.get_completed_membership_payment(test_user.id)
    assert payment is not None


def test_approve_cash_membership_payment(app, test_user):
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    result = payments.approve_cash_payment(payment.id)
    assert result.success is True
    assert payment.status == "completed"


def test_approve_cash_credits_payment(app, test_user):
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="credits",
        payment_method="cash",
        status="pending",
        description="5 shooting credits",
    )
    before = test_user.membership.purchased_credits
    result = payments.approve_cash_payment(payment.id)
    assert result.success is True
    assert test_user.membership.purchased_credits == before + 5


def test_approve_cash_payment_not_found(app):
    result = payments.approve_cash_payment(99999)
    assert result.success is False


def test_reject_cash_payment(app, test_user):
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    result = payments.reject_cash_payment(payment.id)
    assert result.success is True
    assert payment.status == "cancelled"


def test_reject_cash_payment_cannot_reject_completed(app, test_user):
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="membership",
        payment_method="cash",
        status="completed",
    )
    result = payments.reject_cash_payment(payment.id)
    assert result.success is False


def test_credit_quantity_from_description_edge_cases(app):
    from app.services.payment_fulfillment import credit_quantity_from_description

    assert credit_quantity_from_description("5 shooting credits") == 5
    assert credit_quantity_from_description("bad shooting credits") == 1
    assert credit_quantity_from_description(None) == 1


@patch("app.services.payments.emit_payment_side_effects")
def test_approve_cash_payment_renews_active_membership(mock_emit, app, test_user):
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    result = payments.approve_cash_payment(payment.id)
    assert result.success is True
    assert payment.status == "completed"
    mock_emit.assert_called_once()


def test_approve_cash_payment_creates_membership(app, admin_user):
    from app import db
    from app.models import User

    user = User(name="New Cash", email="cashnew@example.com", phone="1", is_active=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    payment = create_payment_for_user(
        db,
        user,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    result = payments.approve_cash_payment(payment.id)
    assert result.success is True
    assert user.membership is not None
    assert user.membership.status == "active"


@patch("app.services.payments.emit_cash_payment_submitted", side_effect=RuntimeError("event"))
def test_initiate_cash_membership_event_failure_still_succeeds(mock_send, app, test_user):
    result = payments.initiate_cash_membership_payment(test_user)
    assert result.success is True


def test_initiate_cash_membership_payment_db_failure(app, test_user):
    with patch("app.repositories.base.BaseRepository.transaction", side_effect=RuntimeError("db")):
        result = payments.initiate_cash_membership_payment(test_user)
    assert result.success is False
    assert "Error creating payment" in result.message


def test_initiate_cash_credit_purchase_db_failure(app, test_user):
    with patch("app.repositories.base.BaseRepository.transaction", side_effect=RuntimeError("db")):
        result = payments.initiate_cash_credit_purchase(test_user, 2)
    assert result.success is False
    assert "Error creating payment" in result.message


def test_get_unfulfilled_online_payment_rows(app, test_user):
    from tests.helpers import create_payment_for_user

    create_payment_for_user(
        db,
        test_user,
        payment_method="online",
        status="pending",
        sumup_checkout_id="chk_rows",
    )
    rows = payments.get_unfulfilled_online_payment_rows()
    assert any(item["payment"].sumup_checkout_id == "chk_rows" for item in rows)


def test_approve_cash_payment_user_not_found(app, test_user):
    from unittest.mock import patch

    from app import db

    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
        amount_cents=1000,
    )
    with patch("app.services.payments.UserRepository.get_by_id", return_value=None):
        result = payments.approve_cash_payment(payment.id)
    assert result.success is False
    assert "User not found" in result.message


# ---------------------------------------------------------------------------
# retry_payment
# ---------------------------------------------------------------------------


class TestRetryPayment:
    def test_reuses_pending_checkout_when_sumup_still_pending(self, app, test_user):
        """If SumUp checkout is still PENDING, return it without creating a new one."""
        from unittest.mock import Mock

        from app.services import payments

        payment = create_payment_for_user(
            db,
            test_user,
            status="pending",
            payment_method="online",
            sumup_checkout_id="chk_live",
            amount_cents=10000,
            description="Annual Membership",
        )
        mock_sumup = Mock()
        mock_sumup.get_checkout.return_value = Mock(status="PENDING")

        result = payments.retry_payment(payment.id, test_user, sumup=mock_sumup)

        assert result.success is True
        assert result.data["checkout_id"] == "chk_live"
        mock_sumup.get_checkout.assert_called_once_with("chk_live")

    def test_creates_new_checkout_when_sumup_checkout_failed(self, app, test_user):
        """If SumUp checkout is FAILED, a new checkout is created and payment updated."""
        from unittest.mock import Mock

        from app.services import payments

        payment = create_payment_for_user(
            db,
            test_user,
            status="pending",
            payment_method="online",
            sumup_checkout_id="chk_dead",
            amount_cents=10000,
            description="Annual Membership",
        )
        mock_sumup = Mock()
        mock_sumup.get_checkout.return_value = Mock(status="FAILED")
        mock_processor = Mock()
        mock_processor.create_checkout.return_value = {"id": "chk_new", "checkout_reference": "ref_new", "status": "PENDING"}

        result = payments.retry_payment(payment.id, test_user, processor=mock_processor, sumup=mock_sumup)

        db.session.refresh(payment)
        assert result.success is True
        assert result.data["checkout_id"] == "chk_new"
        assert payment.sumup_checkout_id == "chk_new"
        assert payment.status == "pending"

    def test_creates_new_checkout_for_failed_status_payment(self, app, test_user):
        """A payment with status=failed always gets a fresh checkout (skip SumUp check)."""
        from unittest.mock import Mock

        from app.services import payments

        payment = create_payment_for_user(
            db,
            test_user,
            status="failed",
            payment_method="online",
            sumup_checkout_id="chk_old",
            amount_cents=5000,
            description="5 shooting credits",
        )
        mock_sumup = Mock()
        mock_processor = Mock()
        mock_processor.create_checkout.return_value = {"id": "chk_fresh", "checkout_reference": "r", "status": "PENDING"}

        result = payments.retry_payment(payment.id, test_user, processor=mock_processor, sumup=mock_sumup)

        db.session.refresh(payment)
        assert result.success is True
        assert result.data["checkout_id"] == "chk_fresh"
        assert payment.status == "pending"
        mock_sumup.get_checkout.assert_not_called()

    def test_returns_not_found_for_missing_payment(self, app, test_user):
        from app.services import payments

        result = payments.retry_payment(999999, test_user)
        assert result.success is False

    def test_returns_not_found_for_wrong_user(self, app, test_user):
        from app.models import User
        from app.services import payments

        other_user = User(name="Other", email="other@example.com", phone="0000000000", is_active=True)
        other_user.set_password("pass")
        db.session.add(other_user)
        db.session.commit()
        payment = create_payment_for_user(db, other_user, status="pending", payment_method="online")

        result = payments.retry_payment(payment.id, test_user)
        assert result.success is False

    def test_cannot_retry_completed_payment(self, app, test_user):
        from app.services import payments

        payment = create_payment_for_user(db, test_user, status="completed", payment_method="online")
        result = payments.retry_payment(payment.id, test_user)
        assert result.success is False
        assert "cannot be retried" in result.message

    def test_cannot_retry_cash_payment(self, app, test_user):
        from app.services import payments

        payment = create_payment_for_user(db, test_user, status="pending", payment_method="cash")
        result = payments.retry_payment(payment.id, test_user)
        assert result.success is False
        assert "online payments" in result.message

    def test_fails_gracefully_when_new_checkout_creation_fails(self, app, test_user):
        """If SumUp create_checkout returns None, retry returns a user-facing error."""
        from unittest.mock import Mock

        from app.services import payments

        payment = create_payment_for_user(db, test_user, status="failed", payment_method="online", sumup_checkout_id="chk_x")
        mock_processor = Mock()
        mock_processor.create_checkout.return_value = None

        result = payments.retry_payment(payment.id, test_user, processor=mock_processor)
        assert result.success is False
        assert "Error creating payment" in result.message

    def test_fails_gracefully_when_db_update_fails(self, app, test_user):
        """If the DB write fails after creating a new checkout, retry returns a user-facing error."""
        from unittest.mock import Mock, patch

        from app.services import payments

        payment = create_payment_for_user(db, test_user, status="failed", payment_method="online", sumup_checkout_id="chk_db_err")
        mock_processor = Mock()
        mock_processor.create_checkout.return_value = {"id": "chk_new2", "checkout_reference": "r", "status": "PENDING"}

        with patch("app.services.payments.BaseRepository.transaction", side_effect=Exception("db down")):
            result = payments.retry_payment(payment.id, test_user, processor=mock_processor)

        assert result.success is False
        assert "Error creating payment" in result.message


def test_cancel_payment_pending_online(app, test_user):
    payment = create_payment_for_user(db, test_user, status="pending", payment_method="online")
    result = payments.cancel_payment(payment.id)
    assert result.success is True
    assert payment.status == "cancelled"


def test_cancel_payment_failed_online(app, test_user):
    payment = create_payment_for_user(db, test_user, status="failed", payment_method="online")
    result = payments.cancel_payment(payment.id)
    assert result.success is True
    assert payment.status == "cancelled"


def test_cancel_payment_pending_cash(app, test_user):
    payment = create_payment_for_user(db, test_user, status="pending", payment_method="cash")
    result = payments.cancel_payment(payment.id)
    assert result.success is True
    assert payment.status == "cancelled"


def test_cancel_payment_not_found(app):
    result = payments.cancel_payment(999999)
    assert result.success is False


def test_cancel_payment_completed_is_rejected(app, test_user):
    payment = create_payment_for_user(db, test_user, status="completed", payment_method="online")
    result = payments.cancel_payment(payment.id)
    assert result.success is False
    assert "pending or failed" in result.message
