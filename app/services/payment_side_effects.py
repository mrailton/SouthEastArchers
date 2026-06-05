"""Payment receipt/ledger side effects (event emission and manual replay)."""

from __future__ import annotations

import logging
from typing import Any

from app.enums import PaymentType
from app.events.payloads import emit_credit_purchased, emit_payment_completed
from app.models import Payment, User
from app.repositories import PaymentRepository, UserRepository
from app.services.payment_fulfillment import credit_quantity_from_description
from app.services.result import ErrorCode, ServiceResult

logger = logging.getLogger(__name__)


def emit_payment_side_effects(
    payment: Payment,
    member: User,
    *,
    quantity: int | None = None,
    already_completed: bool = False,
) -> None:
    """Emit payment_completed or credit_purchased after fulfillment commits."""
    if already_completed:
        return
    try:
        if payment.payment_type == PaymentType.CREDITS:
            resolved_quantity = quantity or credit_quantity_from_description(payment.description)
            emit_credit_purchased(member.id, payment.id, resolved_quantity)
        else:
            emit_payment_completed(member.id, payment.id, payment.payment_type)
    except Exception:
        logger.exception("Failed to emit payment side effects for payment %s", payment.id)


def replay_payment_side_effects(
    payment_id: int,
    *,
    send_mail: bool = True,
) -> ServiceResult[dict[str, Any]]:
    """Re-run mail and ledger recording for a completed payment (handler recovery)."""
    from app.services import finance, mail

    payment = PaymentRepository.get_by_id_with_user(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)
    if payment.status != "completed":
        return ServiceResult.fail("Only completed payments can be replayed.", error_code=ErrorCode.INVALID_STATE)

    member = payment.user or UserRepository.get_by_id(payment.user_id)
    if not member:
        return ServiceResult.fail("User not found.", error_code=ErrorCode.NOT_FOUND)

    mail_sent = False
    if send_mail:
        try:
            if payment.payment_type == PaymentType.CREDITS:
                quantity = credit_quantity_from_description(payment.description)
                mail.send_credit_purchase_receipt(member.id, payment.id, quantity)
            else:
                mail.send_payment_receipt(member.id, payment.id)
            mail_sent = True
        except Exception as exc:
            logger.exception("Replay mail failed for payment %s: %s", payment_id, exc)
            return ServiceResult.fail(f"Failed to send receipt email: {exc}")

    finance_result = finance.record_payment_transactions_for_completed_payment(payment.id, payment.payment_type)
    if not finance_result.success:
        return ServiceResult.fail(finance_result.message)

    return ServiceResult.ok(
        message="Payment side effects replayed successfully.",
        data={"mail_sent": mail_sent, "finance_message": finance_result.message},
    )
