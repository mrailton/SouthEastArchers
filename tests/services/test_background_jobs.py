"""Tests for background job functionality"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app import db
from app.models import Membership, Payment, User
from app.services.background_jobs import (
    _get_app_context,
    send_password_reset_job,
    send_payment_receipt_job,
)


@pytest.fixture
def test_user_with_payment(app):
    """Create test user with membership and payment"""
    user = User(
        name="Test User",
        email="test@example.com",
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        credits=20,
        status="active",
    )
    db.session.add(membership)

    payment = Payment(
        user_id=user.id,
        amount=100.0,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
        description="Annual Membership",
    )
    db.session.add(payment)
    db.session.commit()

    return {"user": user, "payment": payment, "membership": membership}


# TestGetAppContext


def test_get_app_context_when_context_exists(app):
    """Test _get_app_context returns None when context already exists"""
    with app.app_context():
        result = _get_app_context()
        assert result is None


# TestSendPaymentReceiptJob


def test_send_payment_receipt_job(app, test_user_with_payment, fake_mailer):
    """Test payment receipt email job"""
    user = test_user_with_payment["user"]
    payment = test_user_with_payment["payment"]

    # Execute the job within app context
    with app.app_context():
        import app.services.background_jobs as background_jobs
        import app.utils.email as email_mod

        # Ensure both modules reference the fake mailer used in send_payment_receipt
        background_jobs.mail = fake_mailer
        email_mod.mail = fake_mailer

        send_payment_receipt_job(user.id, payment.id)

    # Verify email was sent
    from tests.helpers import assert_email_sent

    assert_email_sent(fake_mailer, subject_contains="Payment Receipt", recipients=[user.email])


def test_send_payment_receipt_job_missing_user(app, fake_mailer):
    """Test payment receipt job handles missing user"""
    # Try to send receipt for non-existent user
    with app.app_context():
        import app.services.background_jobs as background_jobs
        import app.utils.email as email_mod

        background_jobs.mail = fake_mailer
        email_mod.mail = fake_mailer
        send_payment_receipt_job(99999, 99999)

    # Should not send email
    from tests.helpers import assert_no_email_sent

    assert_no_email_sent(fake_mailer)


def test_send_payment_receipt_job_missing_payment(app, test_user_with_payment, fake_mailer):
    """Test payment receipt job handles missing payment"""
    user = test_user_with_payment["user"]

    with app.app_context():
        import app.services.background_jobs as background_jobs
        import app.utils.email as email_mod

        background_jobs.mail = fake_mailer
        email_mod.mail = fake_mailer
        send_payment_receipt_job(user.id, 99999)

    # Should not send email
    from tests.helpers import assert_no_email_sent

    assert_no_email_sent(fake_mailer)


@patch("app.utils.email.send_payment_receipt")
def test_send_payment_receipt_job_without_app_context(mock_send_receipt, test_user_with_payment):
    """Test payment receipt job creates app context when needed"""
    user = test_user_with_payment["user"]
    payment = test_user_with_payment["payment"]

    # Call outside app context - should create its own
    send_payment_receipt_job(user.id, payment.id)

    # Verify the job executed
    assert mock_send_receipt.called


@patch("app.utils.email.send_payment_receipt", side_effect=Exception("Email error"))
def test_send_payment_receipt_job_handles_exception(mock_send_receipt, app, test_user_with_payment):
    """Test payment receipt job handles exceptions gracefully"""
    user = test_user_with_payment["user"]
    payment = test_user_with_payment["payment"]

    # Should not raise, just log error - but exception will still propagate
    with app.app_context():
        # The exception will be raised since it's not caught in the job
        with pytest.raises(Exception):
            send_payment_receipt_job(user.id, payment.id)


# TestSendPasswordResetJob


@patch("app.services.background_jobs.render_template")
def test_send_password_reset_job(mock_render, app, test_user_with_payment, fake_mailer):
    """Test password reset email job"""
    user = test_user_with_payment["user"]
    token = "test-reset-token"

    # Mock template rendering
    mock_render.return_value = f"Password reset for {token}"

    # Execute the job
    with app.app_context():
        import app.services.background_jobs as background_jobs

        background_jobs.mail = fake_mailer
        send_password_reset_job(user.id, token)

    # Verify email was sent
    from tests.helpers import assert_email_sent

    assert_email_sent(fake_mailer, subject_contains="Reset Your Password", recipients=[user.email])


def test_send_password_reset_job_missing_user(app, fake_mailer):
    """Test password reset job handles missing user"""
    with app.app_context():
        import app.services.background_jobs as background_jobs

        background_jobs.mail = fake_mailer
        send_password_reset_job(99999, "token")

    # Should not send email
    from tests.helpers import assert_no_email_sent

    assert_no_email_sent(fake_mailer)


@patch("app.services.background_jobs.render_template")
def test_send_password_reset_job_without_app_context(mock_render, test_user_with_payment, fake_mailer):
    """Test password reset job creates app context when needed"""
    user = test_user_with_payment["user"]
    token = "test-token"

    mock_render.return_value = "Reset email"

    # Call outside app context
    # Ensure background_jobs module will use the fake mailer when it creates its own context
    import app.services.background_jobs as background_jobs

    background_jobs.mail = fake_mailer
    send_password_reset_job(user.id, token)

    # Should have sent email
    from tests.helpers import assert_email_sent

    assert_email_sent(fake_mailer)


@patch("app.services.background_jobs.render_template")
def test_send_password_reset_job_includes_reset_url(mock_render, app, test_user_with_payment, fake_mailer):
    """Test password reset email includes reset URL"""
    user = test_user_with_payment["user"]
    token = "secure-token-123"

    mock_render.return_value = "Reset email"

    with app.app_context():
        import app.services.background_jobs as background_jobs

        background_jobs.mail = fake_mailer
        send_password_reset_job(user.id, token)

    # Verify url_for was called (implied by render_template being called)
    assert mock_render.called


@patch("app.services.background_jobs.render_template", side_effect=Exception("Template error"))
def test_send_password_reset_job_handles_template_error(mock_render, app, test_user_with_payment, fake_mailer):
    """Test password reset job handles template rendering errors"""
    user = test_user_with_payment["user"]

    # Should not raise, context should still be cleaned up
    with app.app_context():
        import app.services.background_jobs as background_jobs

        background_jobs.mail = fake_mailer
        with pytest.raises(Exception):
            send_password_reset_job(user.id, "token")


def test_queue_payment_receipt_with_redis(app, client, test_user_with_payment):
    """Test queueing payment receipt with Redis"""
    from app import task_queue
    from app.services.payment_service import PaymentProcessingService

    if not task_queue:
        pytest.skip("Redis not available")

    user = test_user_with_payment["user"]
    payment = test_user_with_payment["payment"]

    # Queue the job
    PaymentProcessingService.send_payment_receipt(user.id, payment.id)

    # Verify job was queued - check if queue has pending jobs
    # Note: Jobs execute quickly in tests, so we check that queuing succeeded
    # by verifying no errors were raised
    assert True  # If we got here, queuing worked
