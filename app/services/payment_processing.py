from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.enums import PaymentType
from app.models import Payment
from app.repositories import PaymentRepository, UserRepository
from app.services.payment_fulfillment import credit_quantity_from_description, fulfill_payment
from app.services.payment_side_effects import emit_payment_side_effects
from app.services.result import ErrorCode, ServiceResult
from app.services.sumup import SumUpService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckoutFulfillment:
    redirect_url: str
    flash_category: str
    flash_message: str
    session_keys_to_clear: tuple[str, ...]


def _mark_checkout_payment_failed(checkout_id: str) -> None:
    """Mark the pending payment linked to this checkout as failed."""
    try:
        payment = PaymentRepository.get_pending_by_sumup_checkout_id(checkout_id)
        if payment and payment.status == "pending":
            payment.mark_failed()
            PaymentRepository.save()
    except Exception:
        logger.exception("Error marking payment failed for checkout %s", checkout_id)


def _verify_payment_ownership(payment: Payment, user_id: int) -> ServiceResult[None] | None:
    """Return a failure result when payment does not belong to user_id."""
    if payment.user_id != user_id:
        return ServiceResult.fail(
            "Payment does not belong to this user.",
            error_code=ErrorCode.FORBIDDEN,
        )
    return None


_CHECKOUT_FLOWS: dict[str, tuple[str, str, str, tuple[str, ...]]] = {
    "membership_renewal": (
        "membership_renewal_user_id",
        "membership_renewal_payment_id",
        "/member/dashboard",
        ("membership_renewal_user_id", "membership_renewal_payment_id", "checkout_amount", "checkout_description"),
    ),
    "credit_purchase": (
        "credit_purchase_user_id",
        "credit_purchase_payment_id",
        "/member/dashboard",
        (
            "credit_purchase_user_id",
            "credit_purchase_payment_id",
            "credit_purchase_quantity",
            "checkout_amount",
            "checkout_description",
        ),
    ),
}

# Union of all session keys used by any checkout flow — used to clear stale state.
_ALL_CHECKOUT_SESSION_KEYS: tuple[str, ...] = tuple(dict.fromkeys(key for _, _, _, clear_keys in _CHECKOUT_FLOWS.values() for key in clear_keys))


def handle_signup_payment(user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
    payment = PaymentRepository.get_by_id(payment_id)
    user = UserRepository.get_by_id(user_id)

    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.", error_code=ErrorCode.NOT_FOUND)

    if ownership_error := _verify_payment_ownership(payment, user_id):
        return ownership_error

    result = fulfill_payment(
        payment,
        user,
        processor="sumup",
        transaction_id=transaction_id,
        membership_mode="activate_only",
    )
    if not result.success:
        return ServiceResult.fail(result.message, error_code=result.error_code)

    assert result.data is not None
    emit_payment_side_effects(payment, user, already_completed=result.data.already_completed)
    return ServiceResult.ok(message="Payment successful! Your membership is now active. A receipt has been sent to your email.")


def handle_membership_renewal(user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
    payment = PaymentRepository.get_by_id(payment_id)
    user = UserRepository.get_by_id(user_id)

    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.", error_code=ErrorCode.NOT_FOUND)

    if ownership_error := _verify_payment_ownership(payment, user_id):
        return ownership_error

    result = fulfill_payment(
        payment,
        user,
        processor="sumup",
        transaction_id=transaction_id,
        membership_mode="renew_or_create",
    )
    if not result.success:
        return ServiceResult.fail(result.message, error_code=result.error_code)

    assert result.data is not None
    emit_payment_side_effects(payment, user, already_completed=result.data.already_completed)
    return ServiceResult.ok(message="Membership renewed successfully! A receipt has been sent to your email.")


def handle_credit_purchase(user_id: int, payment_id: int, quantity: int, transaction_id: str) -> ServiceResult[None]:
    payment = PaymentRepository.get_by_id(payment_id)
    user = UserRepository.get_by_id(user_id)

    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.", error_code=ErrorCode.NOT_FOUND)

    if ownership_error := _verify_payment_ownership(payment, user_id):
        return ownership_error

    result = fulfill_payment(
        payment,
        user,
        processor="sumup",
        transaction_id=transaction_id,
        quantity=quantity,
    )
    if not result.success:
        return ServiceResult.fail(result.message, error_code=result.error_code)

    assert result.data is not None
    emit_payment_side_effects(
        payment,
        user,
        quantity=result.data.quantity or quantity,
        already_completed=result.data.already_completed,
    )
    return ServiceResult.ok(message=f"Successfully purchased {quantity} credits! A receipt has been sent to your email.")


def _fulfill_pending_online_payment(
    payment: Payment,
    transaction_id: str,
    *,
    quantity: int | None = None,
) -> ServiceResult[None]:
    user = UserRepository.get_by_id(payment.user_id)
    if not user:
        return ServiceResult.fail("User not found.", error_code=ErrorCode.NOT_FOUND)

    if payment.payment_type == PaymentType.CREDITS:
        resolved_quantity = quantity or credit_quantity_from_description(payment.description)
        return handle_credit_purchase(user.id, payment.id, resolved_quantity, transaction_id)

    if not user.is_active:
        return handle_signup_payment(user.id, payment.id, transaction_id)

    return handle_membership_renewal(user.id, payment.id, transaction_id)


def reconcile_sumup_payment(
    payment_id: int,
    *,
    sumup: SumUpService | None = None,
) -> ServiceResult[None]:
    """Verify a pending online payment with SumUp and fulfill it (admin recovery)."""
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)
    if payment.status != "pending" or payment.payment_method != "online":
        return ServiceResult.fail("This payment cannot be reconciled.", error_code=ErrorCode.INVALID_STATE)
    if not payment.sumup_checkout_id:
        return ServiceResult.fail("No SumUp checkout is linked to this payment.")

    sumup_service = sumup or SumUpService()
    checkout = sumup_service.get_checkout(payment.sumup_checkout_id)
    if not checkout:
        return ServiceResult.fail("Could not verify payment status with SumUp.")
    if getattr(checkout, "status", None) != "PAID":
        return ServiceResult.fail("SumUp reports this checkout is not paid.")

    txn_id = getattr(checkout, "transaction_code", None) or getattr(checkout, "transaction_id", None) or payment.sumup_checkout_id
    return _fulfill_pending_online_payment(payment, txn_id)


def _detect_checkout_flow(session: Mapping[str, Any]) -> str | None:
    for flow_name, (user_key, payment_key, _redirect, _keys) in _CHECKOUT_FLOWS.items():
        if session.get(user_key) and session.get(payment_key):
            return flow_name
    return None


def fulfill_checkout(
    *,
    checkout_id: str,
    session: Mapping[str, Any],
    user_id: int | None,
    sumup: SumUpService | None = None,
) -> ServiceResult[CheckoutFulfillment]:
    """Verify SumUp checkout status and complete the matching payment flow."""
    try:
        sumup_service = sumup or SumUpService()
        checkout = sumup_service.get_checkout(checkout_id)
        if not checkout:
            return ServiceResult.fail("Could not verify payment status. Please contact us.")

        status = getattr(checkout, "status", None)
        if status != "PAID":
            if status == "FAILED":
                _mark_checkout_payment_failed(checkout_id)
                return ServiceResult.ok(
                    data=CheckoutFulfillment(
                        redirect_url="/member/dashboard",
                        flash_category="error",
                        flash_message="Your payment was declined. You can retry from your payment history.",
                        session_keys_to_clear=_ALL_CHECKOUT_SESSION_KEYS,
                    )
                )
            elif status == "PENDING":
                message = "Payment is pending. Please contact us if the issue persists."
                return ServiceResult.ok(
                    data=CheckoutFulfillment(
                        redirect_url=f"/payment/checkout/{checkout_id}",
                        flash_category="warning",
                        flash_message=message,
                        session_keys_to_clear=(),
                    )
                )
            else:
                _mark_checkout_payment_failed(checkout_id)
                return ServiceResult.ok(
                    data=CheckoutFulfillment(
                        redirect_url="/member/dashboard",
                        flash_category="error",
                        flash_message="Your payment was not completed. You can retry from your payment history.",
                        session_keys_to_clear=_ALL_CHECKOUT_SESSION_KEYS,
                    )
                )

        if user_id is None:
            return ServiceResult.ok(
                data=CheckoutFulfillment(
                    redirect_url="/auth/login",
                    flash_category="error",
                    flash_message="User session not found. Please try again.",
                    session_keys_to_clear=(),
                )
            )

        txn_id = getattr(checkout, "transaction_code", None) or getattr(checkout, "transaction_id", None) or checkout_id
        flow_name = _detect_checkout_flow(session)
        if flow_name is None:
            payment = PaymentRepository.get_pending_by_sumup_checkout_id(checkout_id)
            if payment is None or payment.user_id != user_id:
                return ServiceResult.ok(
                    data=CheckoutFulfillment(
                        redirect_url="/member/dashboard",
                        flash_category="warning",
                        flash_message="Payment received but could not be matched to your account. Please contact us.",
                        session_keys_to_clear=(),
                    )
                )
            quantity = session.get("credit_purchase_quantity")
            if quantity is not None and not isinstance(quantity, int):
                quantity = int(quantity)
            result = _fulfill_pending_online_payment(payment, txn_id, quantity=quantity)
            user = UserRepository.get_by_id(user_id)
            redirect_url = "/auth/login" if user and not user.is_active else "/member/dashboard"
            return ServiceResult.ok(
                data=CheckoutFulfillment(
                    redirect_url=redirect_url,
                    flash_category="success" if result.success else "error",
                    flash_message=result.message,
                    session_keys_to_clear=(),
                )
            )

        _user_key, payment_key, redirect_url, clear_keys = _CHECKOUT_FLOWS[flow_name]
        payment_id = session.get(payment_key)
        if not isinstance(payment_id, int):
            return ServiceResult.fail("Payment session not found. Please try again.")

        if flow_name == "membership_renewal":
            result = handle_membership_renewal(user_id, payment_id, txn_id)
        else:
            quantity = session.get("credit_purchase_quantity", 1)
            if not isinstance(quantity, int):
                quantity = int(quantity)
            result = handle_credit_purchase(user_id, payment_id, quantity, txn_id)

        return ServiceResult.ok(
            data=CheckoutFulfillment(
                redirect_url=redirect_url,
                flash_category="success" if result.success else "error",
                flash_message=result.message,
                session_keys_to_clear=clear_keys,
            )
        )
    except Exception:
        logger.exception("Error completing checkout")
        return ServiceResult.fail("An error occurred processing your payment. Please try again.")
