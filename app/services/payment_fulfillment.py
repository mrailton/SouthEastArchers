"""Shared payment fulfillment logic for online, cash, and admin flows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.enums import PaymentType
from app.models import Credit, Membership, Payment, User
from app.repositories import BaseRepository, CreditRepository, MembershipRepository
from app.services import settings
from app.services.result import ErrorCode, ServiceResult

logger = logging.getLogger(__name__)

MembershipMode = Literal["activate_only", "activate_or_renew", "renew_or_create"]


@dataclass(frozen=True, slots=True)
class FulfillmentOutcome:
    already_completed: bool = False
    quantity: int | None = None


def credit_quantity_from_description(description: str | None) -> int:
    if description and "shooting credits" in description.lower():
        try:
            return int(description.split()[0])
        except (ValueError, IndexError):
            return 1
    return 1


def _apply_membership_fulfillment(member: User, *, mode: MembershipMode) -> None:
    if mode == "activate_only":
        if member.membership:
            member.membership.activate()
        return

    if member.membership:
        if mode == "activate_or_renew":
            if member.membership.status != "active":
                member.membership.activate()
                return
            expiry_date = settings.calculate_membership_expiry(date.today()).date()
            member.membership.renew(expiry_date=expiry_date)
            return
        expiry_date = settings.calculate_membership_expiry(date.today()).date()
        member.membership.renew(expiry_date=expiry_date)
        return

    start_date = date.today()
    membership = Membership(
        user_id=member.id,
        start_date=start_date,
        expiry_date=settings.calculate_membership_expiry(start_date).date(),
        initial_credits=settings.get("membership_shoots_included"),
        purchased_credits=0,
        status="active",
    )
    MembershipRepository.add(membership)


def _apply_credit_fulfillment(member: User, payment: Payment, quantity: int) -> None:
    if member.membership:
        member.membership.add_credits(quantity)
    CreditRepository.add(Credit(user_id=member.id, amount=quantity, payment_id=payment.id))


def fulfill_payment(
    payment: Payment,
    member: User,
    *,
    processor: str,
    transaction_id: str | None = None,
    quantity: int | None = None,
    membership_mode: MembershipMode = "renew_or_create",
) -> ServiceResult[FulfillmentOutcome]:
    """Mark a pending payment complete and apply membership/credit effects."""
    if payment.status == "completed":
        if transaction_id and payment.external_transaction_id and payment.external_transaction_id != transaction_id:
            return ServiceResult.fail(
                "Payment already completed with a different transaction.",
                error_code=ErrorCode.CONFLICT,
            )
        resolved_quantity = quantity
        if payment.payment_type == PaymentType.CREDITS:
            resolved_quantity = quantity or credit_quantity_from_description(payment.description)
        return ServiceResult.ok(
            data=FulfillmentOutcome(already_completed=True, quantity=resolved_quantity),
            message="Payment already fulfilled.",
        )

    if payment.status != "pending":
        return ServiceResult.fail("This payment cannot be fulfilled.", error_code=ErrorCode.INVALID_STATE)

    resolved_quantity = quantity
    if payment.payment_type == PaymentType.CREDITS:
        resolved_quantity = quantity or credit_quantity_from_description(payment.description)

    try:
        with BaseRepository.transaction():
            payment.mark_completed(transaction_id, processor=processor)
            if payment.payment_type == PaymentType.MEMBERSHIP:
                _apply_membership_fulfillment(member, mode=membership_mode)
            elif payment.payment_type == PaymentType.CREDITS:
                assert resolved_quantity is not None
                _apply_credit_fulfillment(member, payment, resolved_quantity)
    except Exception as exc:
        logger.error("Payment fulfillment failed: %s", exc)
        return ServiceResult.fail("Payment could not be processed. Please try again.")

    return ServiceResult.ok(data=FulfillmentOutcome(quantity=resolved_quantity))
