from __future__ import annotations

import logging
from typing import Any, Protocol

from app.enums import PaymentMethod, PaymentType
from app.events.payloads import emit_cash_payment_submitted
from app.models.payment import Payment
from app.models.user import User
from app.repositories import BaseRepository, PaymentRepository, UserRepository
from app.services import settings
from app.services.payment_fulfillment import fulfill_payment
from app.services.payment_side_effects import emit_payment_side_effects, replay_payment_side_effects
from app.services.result import ErrorCode, ServiceResult
from app.services.sumup import SumUpService

logger = logging.getLogger(__name__)
MAX_CREDIT_QUANTITY = 50


class CheckoutProcessor(Protocol):
    def create_checkout(self, amount: int, currency: str = "EUR", description: str = "") -> dict[str, Any] | None: ...


def get_user_payments(user_id: int) -> list[Payment]:
    return PaymentRepository.get_by_user(user_id)


def retry_payment(
    payment_id: int,
    user: User,
    *,
    processor: CheckoutProcessor | None = None,
    sumup: SumUpService | None = None,
) -> ServiceResult[dict]:
    """Allow a user to retry a pending or failed online payment.

    If the linked SumUp checkout is still PENDING it is reused directly.
    Otherwise a fresh checkout is created and the payment record is updated
    in-place so the full payment history is preserved.
    """
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)
    if payment.user_id != user.id:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.FORBIDDEN)
    if payment.payment_method != PaymentMethod.ONLINE:
        return ServiceResult.fail("Only online payments can be retried.")
    if payment.status in ("completed", "cancelled"):
        return ServiceResult.fail("This payment cannot be retried.")

    # For a still-pending payment, check whether the existing SumUp checkout is live.
    if payment.status == "pending" and payment.sumup_checkout_id:
        sumup_service = sumup or SumUpService()
        checkout = sumup_service.get_checkout(payment.sumup_checkout_id)
        if checkout and getattr(checkout, "status", None) == "PENDING":
            return ServiceResult.ok(
                data={
                    "checkout_id": payment.sumup_checkout_id,
                    "payment_id": payment.id,
                    "user_id": user.id,
                    "amount": payment.amount,
                    "description": payment.description or "",
                }
            )

    # Checkout is failed/expired or payment was explicitly failed — create a new one.
    checkout_processor = processor or SumUpService()
    checkout_data = checkout_processor.create_checkout(
        amount=payment.amount_cents,
        currency=payment.currency,
        description=payment.description or "",
    )
    if not checkout_data:
        return ServiceResult.fail("Error creating payment. Please try again.")

    try:
        with BaseRepository.transaction():
            payment.sumup_checkout_id = checkout_data["id"]
            payment.status = "pending"
    except Exception as exc:
        logger.error("Error updating payment %s for retry: %s", payment_id, exc)
        return ServiceResult.fail("Error creating payment. Please try again.")

    return ServiceResult.ok(
        data={
            "checkout_id": checkout_data["id"],
            "payment_id": payment.id,
            "user_id": user.id,
            "amount": payment.amount,
            "description": payment.description or "",
        }
    )


def initiate_membership_payment(
    user: User,
    *,
    processor: CheckoutProcessor | None = None,
) -> ServiceResult[dict]:
    processor = processor or SumUpService()
    amount_cents: int = settings.get("annual_membership_cost")
    description = f"Annual Membership - {user.name}"

    checkout = processor.create_checkout(amount=amount_cents, currency="EUR", description=description)
    if not checkout:
        return ServiceResult.fail("Error creating payment. Please try again.")

    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.MEMBERSHIP,
        payment_method=PaymentMethod.ONLINE,
        description=description,
        status="pending",
        sumup_checkout_id=checkout.get("id"),
    )
    try:
        with BaseRepository.transaction():
            PaymentRepository.add(payment)
    except Exception as exc:
        logger.error("Error saving membership payment: %s", exc)
        return ServiceResult.fail("Error creating payment. Please try again.")

    return ServiceResult.ok(
        data={
            "checkout_id": checkout.get("id"),
            "payment_id": payment.id,
            "user_id": user.id,
            "amount": amount_cents / 100.0,
            "description": description,
        }
    )


def initiate_credit_purchase(
    user: User,
    quantity: int,
    *,
    processor: CheckoutProcessor | None = None,
) -> ServiceResult[dict]:
    processor = processor or SumUpService()
    amount_cents: int = quantity * settings.get("additional_shoot_cost")
    description = f"{quantity} credits - {user.name}"

    checkout = processor.create_checkout(amount=amount_cents, currency="EUR", description=description)
    if not checkout:
        return ServiceResult.fail("Error creating payment. Please try again.")

    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.CREDITS,
        payment_method=PaymentMethod.ONLINE,
        description=f"{quantity} shooting credits",
        status="pending",
        sumup_checkout_id=checkout.get("id"),
    )
    try:
        with BaseRepository.transaction():
            PaymentRepository.add(payment)
    except Exception as exc:
        logger.error("Error saving credit payment: %s", exc)
        return ServiceResult.fail("Error creating payment. Please try again.")

    return ServiceResult.ok(
        data={
            "checkout_id": checkout.get("id"),
            "payment_id": payment.id,
            "user_id": user.id,
            "quantity": quantity,
            "amount": amount_cents / 100.0,
            "description": description,
        }
    )


def initiate_cash_membership_payment(user: User) -> ServiceResult[dict]:
    amount_cents: int = settings.get("annual_membership_cost")
    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.MEMBERSHIP,
        payment_method=PaymentMethod.CASH,
        description=f"Annual Membership (Cash) - {user.name}",
        status="pending",
    )
    try:
        with BaseRepository.transaction():
            PaymentRepository.add(payment)
            PaymentRepository.flush()
    except Exception as exc:
        logger.error("Error creating cash membership payment: %s", exc)
        return ServiceResult.fail("Error creating payment. Please try again.")

    try:
        emit_cash_payment_submitted(user.id, payment.id)
    except Exception:
        logger.exception("Failed to emit cash_payment_submitted event")

    return ServiceResult.ok(
        data={
            "payment_id": payment.id,
            "amount": amount_cents / 100.0,
            "instructions": settings.get("cash_payment_instructions"),
        }
    )


def initiate_cash_credit_purchase(user: User, quantity: int) -> ServiceResult[dict]:
    amount_cents: int = quantity * settings.get("additional_shoot_cost")
    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.CREDITS,
        payment_method=PaymentMethod.CASH,
        description=f"{quantity} shooting credits (Cash)",
        status="pending",
    )
    try:
        with BaseRepository.transaction():
            PaymentRepository.add(payment)
            PaymentRepository.flush()
    except Exception as exc:
        logger.error("Error creating cash credit payment: %s", exc)
        return ServiceResult.fail("Error creating payment. Please try again.")

    try:
        emit_cash_payment_submitted(user.id, payment.id)
    except Exception:
        logger.exception("Failed to emit cash_payment_submitted event")

    return ServiceResult.ok(
        data={
            "payment_id": payment.id,
            "quantity": quantity,
            "amount": amount_cents / 100.0,
            "instructions": settings.get("cash_payment_instructions"),
        }
    )


def get_unfulfilled_online_payment_rows() -> list[dict[str, Any]]:
    return PaymentRepository.get_pending_online_with_users()


def validate_credit_quantity(quantity: int) -> ServiceResult[int]:
    if quantity < 1 or quantity > MAX_CREDIT_QUANTITY:
        return ServiceResult.fail(f"Quantity must be between 1 and {MAX_CREDIT_QUANTITY}.")
    return ServiceResult.ok(data=quantity)


def get_pending_cash_payment_rows() -> list[dict[str, Any]]:
    return PaymentRepository.get_pending_cash_with_users()


def get_completed_membership_payment(user_id: int) -> Payment | None:
    return PaymentRepository.get_completed_for_user(user_id, PaymentType.MEMBERSHIP)


def approve_cash_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)
    if payment.payment_method != PaymentMethod.CASH:
        return ServiceResult.fail("This payment cannot be approved.", error_code=ErrorCode.INVALID_STATE)
    if payment.status not in ("pending", "completed"):
        return ServiceResult.fail("This payment cannot be approved.", error_code=ErrorCode.INVALID_STATE)

    member = UserRepository.get_by_id(payment.user_id)
    if not member:
        return ServiceResult.fail("User not found.", error_code=ErrorCode.NOT_FOUND)

    result = fulfill_payment(
        payment,
        member,
        processor="cash",
        membership_mode="activate_or_renew",
    )
    if not result.success:
        logger.error("Error approving payment: %s", result.message)
        return ServiceResult.fail("Error approving payment. Please try again.", error_code=result.error_code)

    assert result.data is not None
    if not result.data.already_completed:
        emit_payment_side_effects(payment, member)
    return ServiceResult.ok(data={"member_name": member.name}, message=f"Payment approved for {member.name}!")


def reject_cash_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)
    if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
        return ServiceResult.fail("This payment cannot be rejected.")
    member = UserRepository.get_by_id(payment.user_id)
    payment.status = "cancelled"
    PaymentRepository.save()
    member_name = member.name if member else "user"
    return ServiceResult.ok(data={"member_name": member_name}, message=f"Payment rejected for {member_name}.")


def cancel_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
    """Admin-initiated cancellation of any pending or failed payment."""
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)
    if payment.status not in ("pending", "failed"):
        return ServiceResult.fail("Only pending or failed payments can be cancelled.")
    member = UserRepository.get_by_id(payment.user_id)
    payment.status = "cancelled"
    PaymentRepository.save()
    member_name = member.name if member else "user"
    return ServiceResult.ok(data={"member_name": member_name}, message=f"Payment cancelled for {member_name}.")


def replay_completed_payment_side_effects(payment_id: int, *, send_mail: bool = True) -> ServiceResult[dict[str, Any]]:
    """Re-run receipt email and ledger entries for a completed payment."""
    return replay_payment_side_effects(payment_id, send_mail=send_mail)
