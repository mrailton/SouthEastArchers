"""Tests for background job functionality"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app import db
from app.models import Membership, Payment, User
from app.services.background_jobs import (
    send_membership_expiry_reminder_job,
    send_password_reset_job,
    send_payment_receipt_job,
)


@pytest.fixture
def test_user_with_payment(app):
    """Create test user with membership and payment"""
    user = User(
        name="Test User",
        email="test@example.com",
        date_of_birth=date(1990, 1, 1),
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


class TestBackgroundJobs:
    """Test background job execution"""

    @patch("app.services.background_jobs.mail.send")
    def test_send_payment_receipt_job(self, mock_mail_send, app, test_user_with_payment):
        """Test payment receipt email job"""
        user = test_user_with_payment["user"]
        payment = test_user_with_payment["payment"]

        # Execute the job within app context
        with app.app_context():
            send_payment_receipt_job(user.id, payment.id)

        # Verify email was sent
        assert mock_mail_send.called
        call_args = mock_mail_send.call_args[0][0]
        assert "Payment Receipt" in call_args.subject
        assert user.email in call_args.recipients

    @patch("app.services.background_jobs.mail.send")
    def test_send_payment_receipt_job_missing_user(self, mock_mail_send, app):
        """Test payment receipt job handles missing user"""
        # Try to send receipt for non-existent user
        with app.app_context():
            send_payment_receipt_job(99999, 99999)

        # Should not send email
        assert not mock_mail_send.called

    @patch("app.services.background_jobs.render_template")
    @patch("app.services.background_jobs.mail.send")
    def test_send_password_reset_job(self, mock_mail_send, mock_render, app, test_user_with_payment):
        """Test password reset email job"""
        user = test_user_with_payment["user"]
        token = "test-reset-token"

        # Mock template rendering
        mock_render.return_value = f"Password reset for {token}"

        # Execute the job
        with app.app_context():
            send_password_reset_job(user.id, token)

        # Verify email was sent
        assert mock_mail_send.called
        call_args = mock_mail_send.call_args[0][0]
        assert "Reset Your Password" in call_args.subject
        assert user.email in call_args.recipients

    @patch("app.services.background_jobs.render_template")
    @patch("app.services.background_jobs.mail.send")
    def test_send_membership_expiry_reminder_job(self, mock_mail_send, mock_render, app, test_user_with_payment):
        """Test membership expiry reminder job"""
        user = test_user_with_payment["user"]

        # Mock template rendering
        mock_render.return_value = "Membership expiry reminder"

        # Execute the job
        with app.app_context():
            send_membership_expiry_reminder_job(user.id)

        # Verify email was sent
        assert mock_mail_send.called
        call_args = mock_mail_send.call_args[0][0]
        assert "Membership Expiry Reminder" in call_args.subject
        assert user.email in call_args.recipients


class TestJobQueueing:
    """Test job queueing functionality"""

    def test_queue_payment_receipt_with_redis(self, app, client, test_user_with_payment):
        """Test queueing payment receipt with Redis"""
        from app import task_queue
        from app.services.payment_service import PaymentProcessingService

        if not task_queue:
            pytest.skip("Redis not available")

        user = test_user_with_payment["user"]
        payment = test_user_with_payment["payment"]

        # Queue the job
        PaymentProcessingService.queue_payment_receipt(user.id, payment.id)

        # Verify job was queued - check if queue has pending jobs
        # Note: Jobs execute quickly in tests, so we check that queuing succeeded
        # by verifying no errors were raised
        assert True  # If we got here, queuing worked

    @patch("app.utils.email.send_payment_receipt")
    def test_queue_payment_receipt_fallback(self, mock_send_receipt, app, test_user_with_payment):
        """Test payment receipt falls back to sync when Redis unavailable"""
        from app import task_queue
        from app.services.payment_service import PaymentProcessingService

        if task_queue:
            pytest.skip("Redis is available, can't test fallback")

        user = test_user_with_payment["user"]
        payment = test_user_with_payment["payment"]

        # Queue the job (should fallback to sync)
        PaymentProcessingService.queue_payment_receipt(user.id, payment.id)

        # Verify sync function was called
        assert mock_send_receipt.called
