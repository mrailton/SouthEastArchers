from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from app.enums import PaymentType
from app.events import (
    cash_payment_submitted,
    credit_purchased,
    membership_activated,
    password_reset_requested,
    payment_completed,
    user_activated,
    user_registered,
)
from app.events.background import defer_handler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------


def _on_user_registered(sender: Any, **kwargs: Any) -> None:
    """Notify admins that a new member has signed up."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    try:
        mail.send_new_member_notification(user_id)
    except Exception as e:
        logger.error(f"Event handler _on_user_registered failed: {e}")


def _on_user_activated(sender: Any, **kwargs: Any) -> None:
    """Send a welcome email when a user account is activated."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    try:
        mail.send_welcome_email(user_id)
    except Exception as e:
        logger.error(f"Event handler _on_user_activated failed: {e}")


def _on_payment_completed(sender: Any, **kwargs: Any) -> None:
    """Send a payment receipt when a payment is completed."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    payment_id: int = kwargs["payment_id"]
    try:
        mail.send_payment_receipt(user_id, payment_id)
    except Exception as e:
        logger.error(f"Event handler _on_payment_completed failed: {e}")

    _record_payment_financial_transactions(payment_id, kwargs.get("payment_type", PaymentType.MEMBERSHIP))


def _on_credit_purchased(sender: Any, **kwargs: Any) -> None:
    """Send a credit purchase receipt."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    payment_id: int = kwargs["payment_id"]
    quantity: int = kwargs["quantity"]
    try:
        mail.send_credit_purchase_receipt(user_id, payment_id, quantity)
    except Exception as e:
        logger.error(f"Event handler _on_credit_purchased failed: {e}")

    _record_payment_financial_transactions(payment_id, PaymentType.CREDITS)


def _on_cash_payment_submitted(sender: Any, **kwargs: Any) -> None:
    """Send a cash payment pending confirmation email."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    payment_id: int = kwargs["payment_id"]
    try:
        mail.send_cash_payment_pending_email(user_id, payment_id)
    except Exception as e:
        logger.error(f"Event handler _on_cash_payment_submitted failed: {e}")


def _on_password_reset_requested(sender: Any, **kwargs: Any) -> None:
    """Send a password reset email."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    token: str = kwargs["token"]
    try:
        mail.send_password_reset(user_id, token)
    except Exception as e:
        logger.error(f"Event handler _on_password_reset_requested failed: {e}")


def _on_membership_activated(sender: Any, **kwargs: Any) -> None:
    """Send a payment receipt when a membership is activated (if a payment exists)."""
    from app.services import mail

    user_id: int = kwargs["user_id"]
    payment_id: int | None = kwargs.get("payment_id")
    if payment_id is not None:
        try:
            mail.send_payment_receipt(user_id, payment_id)
        except Exception as e:
            logger.error(f"Event handler _on_membership_activated failed: {e}")


def _record_payment_financial_transactions(payment_id: int, payment_type: str) -> None:
    """Record financial transactions for completed payments."""
    from app.services import finance

    try:
        result = finance.record_payment_transactions_for_completed_payment(payment_id, payment_type)
        if not result.success:
            logger.warning("Auto-record financial transactions skipped for payment %s: %s", payment_id, result.message)
    except Exception as e:
        logger.error("Failed to record financial transactions for payment %s: %s", payment_id, e)


def _make_deferred_receiver(handler) -> Callable[..., None]:
    def receiver(sender: Any, **kwargs: Any) -> None:
        from app.core.config import get_settings
        from app.events.background import run_handler_safe

        if get_settings().is_testing:
            run_handler_safe(handler, sender, **kwargs)
        else:
            defer_handler(handler, sender, **kwargs)

    receiver.__name__ = f"deferred_{handler.__name__}"
    return receiver


# Strong references prevent blinker from garbage-collecting weak receiver refs.
_RECEIVERS: list[tuple[Any, Callable[..., None]]] = [
    (user_registered, _make_deferred_receiver(_on_user_registered)),
    (user_activated, _make_deferred_receiver(_on_user_activated)),
    (payment_completed, _make_deferred_receiver(_on_payment_completed)),
    (credit_purchased, _make_deferred_receiver(_on_credit_purchased)),
    (cash_payment_submitted, _make_deferred_receiver(_on_cash_payment_submitted)),
    (password_reset_requested, _make_deferred_receiver(_on_password_reset_requested)),
    (membership_activated, _make_deferred_receiver(_on_membership_activated)),
]


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

    for signal, receiver in _RECEIVERS:
        signal.connect(receiver)
