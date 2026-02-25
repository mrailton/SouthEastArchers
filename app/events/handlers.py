"""Event handlers that connect domain signals to side effects (e.g., email sending).

All handlers are registered when :func:`connect_handlers` is called during app
startup.  They keep side-effect logic out of the core services.
"""

from __future__ import annotations

from typing import Any

from flask import current_app

from app.events import (
    cash_payment_submitted,
    credit_purchased,
    membership_activated,
    password_reset_requested,
    payment_completed,
    user_activated,
    user_registered,
)

# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------


def _on_user_registered(sender: Any, **kwargs: Any) -> None:
    """Notify admins that a new member has signed up."""
    from app.services.mail_service import send_new_member_notification

    user_id: int = kwargs["user_id"]
    try:
        send_new_member_notification(user_id)
    except Exception as e:
        current_app.logger.error(f"Event handler _on_user_registered failed: {e}")


def _on_user_activated(sender: Any, **kwargs: Any) -> None:
    """Send a welcome email when a user account is activated."""
    from app.services.mail_service import send_welcome_email

    user_id: int = kwargs["user_id"]
    try:
        send_welcome_email(user_id)
    except Exception as e:
        current_app.logger.error(f"Event handler _on_user_activated failed: {e}")


def _on_payment_completed(sender: Any, **kwargs: Any) -> None:
    """Send a payment receipt when a payment is completed."""
    from app.services.mail_service import send_payment_receipt

    user_id: int = kwargs["user_id"]
    payment_id: int = kwargs["payment_id"]
    try:
        send_payment_receipt(user_id, payment_id)
    except Exception as e:
        current_app.logger.error(f"Event handler _on_payment_completed failed: {e}")


def _on_credit_purchased(sender: Any, **kwargs: Any) -> None:
    """Send a credit purchase receipt."""
    from app.services.mail_service import send_credit_purchase_receipt

    user_id: int = kwargs["user_id"]
    payment_id: int = kwargs["payment_id"]
    quantity: int = kwargs["quantity"]
    try:
        send_credit_purchase_receipt(user_id, payment_id, quantity)
    except Exception as e:
        current_app.logger.error(f"Event handler _on_credit_purchased failed: {e}")


def _on_cash_payment_submitted(sender: Any, **kwargs: Any) -> None:
    """Send a cash payment pending confirmation email."""
    from app.services.mail_service import send_cash_payment_pending_email

    user_id: int = kwargs["user_id"]
    payment_id: int = kwargs["payment_id"]
    try:
        send_cash_payment_pending_email(user_id, payment_id)
    except Exception as e:
        current_app.logger.error(f"Event handler _on_cash_payment_submitted failed: {e}")


def _on_password_reset_requested(sender: Any, **kwargs: Any) -> None:
    """Send a password reset email."""
    from app.services.mail_service import send_password_reset

    user_id: int = kwargs["user_id"]
    token: str = kwargs["token"]
    try:
        send_password_reset(user_id, token)
    except Exception as e:
        current_app.logger.error(f"Event handler _on_password_reset_requested failed: {e}")


def _on_membership_activated(sender: Any, **kwargs: Any) -> None:
    """Send a payment receipt when a membership is activated (if a payment exists)."""
    from app.services.mail_service import send_payment_receipt

    user_id: int = kwargs["user_id"]
    payment_id: int | None = kwargs.get("payment_id")
    if payment_id is not None:
        try:
            send_payment_receipt(user_id, payment_id)
        except Exception as e:
            current_app.logger.error(f"Event handler _on_membership_activated failed: {e}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_handlers_connected = False


def connect_handlers() -> None:
    """Wire up all domain event handlers.  Called once during app creation.

    Idempotent — safe to call multiple times (e.g., in test fixtures).
    """
    global _handlers_connected
    if _handlers_connected:
        return
    _handlers_connected = True

    user_registered.connect(_on_user_registered)
    user_activated.connect(_on_user_activated)
    payment_completed.connect(_on_payment_completed)
    credit_purchased.connect(_on_credit_purchased)
    cash_payment_submitted.connect(_on_cash_payment_submitted)
    password_reset_requested.connect(_on_password_reset_requested)
    membership_activated.connect(_on_membership_activated)
