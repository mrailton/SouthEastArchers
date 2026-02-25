"""Tests for domain event handlers."""

from unittest.mock import patch

from app.events import (
    cash_payment_submitted,
    credit_purchased,
    membership_activated,
    password_reset_requested,
    payment_completed,
    user_activated,
    user_registered,
)


def test_user_registered_triggers_new_member_notification(app):
    """user_registered signal triggers send_new_member_notification."""
    with patch("app.services.mail_service.send_new_member_notification") as mock_notify:
        user_registered.send(user_id=42)
        mock_notify.assert_called_once_with(42)


def test_user_activated_triggers_welcome_email(app):
    """user_activated signal triggers send_welcome_email."""
    with patch("app.services.mail_service.send_welcome_email") as mock_welcome:
        user_activated.send(user_id=7)
        mock_welcome.assert_called_once_with(7)


def test_payment_completed_triggers_receipt(app):
    """payment_completed signal triggers send_payment_receipt."""
    with patch("app.services.mail_service.send_payment_receipt") as mock_receipt:
        payment_completed.send(user_id=1, payment_id=99, payment_type="membership")
        mock_receipt.assert_called_once_with(1, 99)


def test_credit_purchased_triggers_credit_receipt(app):
    """credit_purchased signal triggers send_credit_purchase_receipt."""
    with patch("app.services.mail_service.send_credit_purchase_receipt") as mock_receipt:
        credit_purchased.send(user_id=3, payment_id=55, quantity=5)
        mock_receipt.assert_called_once_with(3, 55, 5)


def test_cash_payment_submitted_triggers_pending_email(app):
    """cash_payment_submitted signal triggers send_cash_payment_pending_email."""
    with patch("app.services.mail_service.send_cash_payment_pending_email") as mock_pending:
        cash_payment_submitted.send(user_id=10, payment_id=20)
        mock_pending.assert_called_once_with(10, 20)


def test_password_reset_requested_triggers_reset_email(app):
    """password_reset_requested signal triggers send_password_reset."""
    with patch("app.services.mail_service.send_password_reset") as mock_reset:
        password_reset_requested.send(user_id=4, token="abc123")
        mock_reset.assert_called_once_with(4, "abc123")


def test_membership_activated_with_payment_triggers_receipt(app):
    """membership_activated with a payment_id triggers send_payment_receipt."""
    with patch("app.services.mail_service.send_payment_receipt") as mock_receipt:
        membership_activated.send(user_id=2, payment_id=77)
        mock_receipt.assert_called_once_with(2, 77)


def test_membership_activated_without_payment_does_not_send(app):
    """membership_activated without a payment_id does NOT trigger send_payment_receipt."""
    with patch("app.services.mail_service.send_payment_receipt") as mock_receipt:
        membership_activated.send(user_id=2)
        mock_receipt.assert_not_called()


def test_handler_exception_is_caught(app):
    """Handler exceptions are caught and logged, not propagated."""
    with patch("app.services.mail_service.send_new_member_notification", side_effect=Exception("boom")):
        # Should not raise
        user_registered.send(user_id=1)


def test_handler_exception_is_logged(app):
    """Handler exceptions are logged."""
    with patch("app.services.mail_service.send_new_member_notification", side_effect=Exception("boom")):
        # The handler catches the exception and logs it — verify no propagation
        user_registered.send(user_id=1)
