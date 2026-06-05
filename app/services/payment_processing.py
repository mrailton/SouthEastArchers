from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.events import credit_purchased, payment_completed
from app.models import Credit, Membership
from app.repositories import BaseRepository, CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services import settings
from app.services.result import ServiceResult
from app.services.sumup import SumUpService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckoutFulfillment:
    redirect_url: str
    flash_category: str
    flash_message: str
    session_keys_to_clear: tuple[str, ...]


_CHECKOUT_FLOWS: dict[str, tuple[str, str, str, tuple[str, ...]]] = {
    "signup": (
        "signup_user_id",
        "signup_payment_id",
        "/auth/login",
        ("signup_user_id", "signup_payment_id", "checkout_amount", "checkout_description"),
    ),
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


def handle_signup_payment(user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
    payment = PaymentRepository.get_by_id(payment_id)
    user = UserRepository.get_by_id(user_id)

    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.")

    try:
        with BaseRepository.transaction():
            payment.mark_completed(transaction_id, processor="sumup")
            if user.membership:
                user.membership.activate()
    except Exception as exc:
        logger.error("Signup payment commit failed: %s", exc)
        return ServiceResult.fail("Payment could not be processed. Please try again.")

    try:
        payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
    except Exception as exc:
        logger.error("Failed to emit payment_completed event: %s", exc)

    return ServiceResult.ok(message="Payment successful! Your membership is now active. A receipt has been sent to your email.")


def handle_membership_renewal(user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
    payment = PaymentRepository.get_by_id(payment_id)
    user = UserRepository.get_by_id(user_id)

    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.")

    try:
        with BaseRepository.transaction():
            payment.mark_completed(transaction_id, processor="sumup")

            if user.membership:
                expiry_date = settings.calculate_membership_expiry(date.today()).date()
                user.membership.renew(expiry_date=expiry_date)
            else:
                start_date = date.today()
                membership = Membership(
                    user_id=user.id,
                    start_date=start_date,
                    expiry_date=settings.calculate_membership_expiry(start_date).date(),
                    status="active",
                )
                MembershipRepository.add(membership)
    except Exception as exc:
        logger.error("Membership renewal commit failed: %s", exc)
        return ServiceResult.fail("Renewal could not be processed. Please try again.")

    try:
        payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
    except Exception as exc:
        logger.error("Failed to emit payment_completed event: %s", exc)

    return ServiceResult.ok(message="Membership renewed successfully! A receipt has been sent to your email.")


def handle_credit_purchase(user_id: int, payment_id: int, quantity: int, transaction_id: str) -> ServiceResult[None]:
    payment = PaymentRepository.get_by_id(payment_id)
    user = UserRepository.get_by_id(user_id)

    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.")

    try:
        with BaseRepository.transaction():
            payment.mark_completed(transaction_id, processor="sumup")

            if user.membership:
                user.membership.add_credits(quantity)

            credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
            CreditRepository.add(credit)
    except Exception as exc:
        logger.error("Credit purchase commit failed: %s", exc)
        return ServiceResult.fail("Credit purchase could not be processed. Please try again.")

    try:
        credit_purchased.send(user_id=user_id, payment_id=payment.id, quantity=quantity)
    except Exception as exc:
        logger.error("Failed to emit credit_purchased event: %s", exc)

    return ServiceResult.ok(message=f"Successfully purchased {quantity} credits! A receipt has been sent to your email.")


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
                message = "Payment declined: Payment was not approved"
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
                message = "Payment failed: Payment was not approved"
            return ServiceResult.ok(
                data=CheckoutFulfillment(
                    redirect_url=f"/payment/checkout/{checkout_id}",
                    flash_category="error",
                    flash_message=message,
                    session_keys_to_clear=(),
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
            return ServiceResult.ok(
                data=CheckoutFulfillment(
                    redirect_url="/member/dashboard",
                    flash_category="success",
                    flash_message="Payment processed successfully!",
                    session_keys_to_clear=(),
                )
            )

        _user_key, payment_key, redirect_url, clear_keys = _CHECKOUT_FLOWS[flow_name]
        payment_id = session.get(payment_key)
        if not isinstance(payment_id, int):
            return ServiceResult.fail("Payment session not found. Please try again.")

        if flow_name == "signup":
            result = handle_signup_payment(user_id, payment_id, txn_id)
        elif flow_name == "membership_renewal":
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
