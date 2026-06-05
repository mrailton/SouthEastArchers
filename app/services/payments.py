from __future__ import annotations

import logging
from datetime import date
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import get_setting
from app.enums import PaymentMethod, PaymentType
from app.events import cash_payment_submitted, credit_purchased, payment_completed
from app.models.credit import Credit
from app.models.membership import Membership
from app.models.payment import Payment
from app.models.user import User
from app.repositories import CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services import settings
from app.services.result import ServiceResult
from app.services.sumup import SumUpService

logger = logging.getLogger(__name__)
MAX_CREDIT_QUANTITY = 50


class CheckoutProcessor(Protocol):
    def create_checkout(self, amount: int, currency: str = "EUR", description: str = "") -> dict[str, Any] | None: ...


def create_checkout(
    amount_cents: int,
    description: str,
    *,
    processor: CheckoutProcessor | None = None,
) -> dict[str, Any] | None:
    processor = processor or SumUpService()
    return processor.create_checkout(amount=amount_cents, currency="EUR", description=description)


def get_user_payments(db: Session, user_id: int) -> list[Payment]:
    return list(db.scalars(select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())).all())


def initiate_membership_payment(
    db: Session,
    user: User,
    *,
    processor: CheckoutProcessor | None = None,
) -> ServiceResult[dict]:
    processor = processor or SumUpService()
    amount_cents: int = get_setting(db, "annual_membership_cost")
    description = f"Annual Membership - {user.name}"

    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.MEMBERSHIP,
        payment_method=PaymentMethod.ONLINE,
        description=description,
        status="pending",
    )
    db.add(payment)
    db.flush()

    checkout = processor.create_checkout(amount=amount_cents, currency="EUR", description=description)
    if checkout:
        return ServiceResult.ok(
            data={
                "checkout_id": checkout.get("id"),
                "payment_id": payment.id,
                "user_id": user.id,
                "amount": amount_cents / 100.0,
                "description": description,
            }
        )

    db.delete(payment)
    db.flush()
    return ServiceResult.fail("Error creating payment. Please try again.")


def initiate_credit_purchase(
    db: Session,
    user: User,
    quantity: int,
    *,
    processor: CheckoutProcessor | None = None,
) -> ServiceResult[dict]:
    processor = processor or SumUpService()
    amount_cents: int = quantity * get_setting(db, "additional_shoot_cost")
    description = f"{quantity} credits - {user.name}"

    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.CREDITS,
        payment_method=PaymentMethod.ONLINE,
        description=f"{quantity} shooting credits",
        status="pending",
    )
    db.add(payment)
    db.flush()

    checkout = processor.create_checkout(amount=amount_cents, currency="EUR", description=description)
    if checkout:
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

    db.delete(payment)
    db.flush()
    return ServiceResult.fail("Error creating payment. Please try again.")


def initiate_cash_membership_payment(db: Session, user: User) -> ServiceResult[dict]:
    amount_cents: int = get_setting(db, "annual_membership_cost")
    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.MEMBERSHIP,
        payment_method=PaymentMethod.CASH,
        description=f"Annual Membership (Cash) - {user.name}",
        status="pending",
    )
    db.add(payment)
    db.flush()

    try:
        cash_payment_submitted.send(user_id=user.id, payment_id=payment.id)
    except Exception:
        logger.exception("Failed to emit cash_payment_submitted event")

    return ServiceResult.ok(
        data={
            "payment_id": payment.id,
            "amount": amount_cents / 100.0,
            "instructions": get_setting(db, "cash_payment_instructions"),
        }
    )


def initiate_cash_credit_purchase(db: Session, user: User, quantity: int) -> ServiceResult[dict]:
    amount_cents: int = quantity * get_setting(db, "additional_shoot_cost")
    payment = Payment(
        user_id=user.id,
        amount_cents=amount_cents,
        currency="EUR",
        payment_type=PaymentType.CREDITS,
        payment_method=PaymentMethod.CASH,
        description=f"{quantity} shooting credits (Cash)",
        status="pending",
    )
    db.add(payment)
    db.flush()

    try:
        cash_payment_submitted.send(user_id=user.id, payment_id=payment.id)
    except Exception:
        logger.exception("Failed to emit cash_payment_submitted event")

    return ServiceResult.ok(
        data={
            "payment_id": payment.id,
            "quantity": quantity,
            "amount": amount_cents / 100.0,
            "instructions": get_setting(db, "cash_payment_instructions"),
        }
    )


def validate_credit_quantity(quantity: int) -> ServiceResult[int]:
    if quantity < 1 or quantity > MAX_CREDIT_QUANTITY:
        return ServiceResult.fail(f"Quantity must be between 1 and {MAX_CREDIT_QUANTITY}.")
    return ServiceResult.ok(data=quantity)


def get_pending_cash_payment_rows() -> list[dict[str, Any]]:
    payments = PaymentRepository.get_pending_cash()
    return [{"payment": payment, "user": UserRepository.get_by_id(payment.user_id)} for payment in payments]


def get_completed_membership_payment(user_id: int) -> Payment | None:
    return PaymentRepository.get_completed_for_user(user_id, PaymentType.MEMBERSHIP)


def approve_cash_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.")
    if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
        return ServiceResult.fail("This payment cannot be approved.")

    member = UserRepository.get_by_id(payment.user_id)
    if not member:
        return ServiceResult.fail("User not found.")

    try:
        payment.mark_completed(processor="cash")
        if payment.payment_type == PaymentType.MEMBERSHIP:
            if member.membership:
                if member.membership.status != "active":
                    member.membership.activate()
                else:
                    expiry_date = settings.calculate_membership_expiry(date.today()).date()
                    member.membership.renew(expiry_date=expiry_date)
            else:
                expiry_date = settings.calculate_membership_expiry(date.today()).date()
                membership = Membership(
                    user_id=member.id,
                    start_date=date.today(),
                    expiry_date=expiry_date,
                    initial_credits=settings.get("membership_shoots_included"),
                    purchased_credits=0,
                    status="active",
                )
                MembershipRepository.add(membership)
        elif payment.payment_type == PaymentType.CREDITS:
            quantity = _credit_quantity_from_description(payment.description)
            if member.membership:
                member.membership.add_credits(quantity)
            CreditRepository.add(Credit(user_id=member.id, amount=quantity, payment_id=payment.id))

        PaymentRepository.save()
        _emit_payment_completed_events(payment, member)
        return ServiceResult.ok(data={"member_name": member.name}, message=f"Payment approved for {member.name}!")
    except Exception as exc:
        logger.error("Error approving payment: %s", exc)
        return ServiceResult.fail(f"Error approving payment: {exc}")


def reject_cash_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.")
    if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
        return ServiceResult.fail("This payment cannot be rejected.")
    member = UserRepository.get_by_id(payment.user_id)
    payment.status = "cancelled"
    PaymentRepository.save()
    member_name = member.name if member else "user"
    return ServiceResult.ok(data={"member_name": member_name}, message=f"Payment rejected for {member_name}.")


def _credit_quantity_from_description(description: str | None) -> int:
    if description and "shooting credits" in description.lower():
        try:
            return int(description.split()[0])
        except ValueError, IndexError:
            return 1
    return 1


def _emit_payment_completed_events(payment: Payment, member: User) -> None:
    try:
        if payment.payment_type == PaymentType.CREDITS:
            quantity = _credit_quantity_from_description(payment.description)
            credit_purchased.send(user_id=member.id, payment_id=payment.id, quantity=quantity)
        else:
            payment_completed.send(user_id=member.id, payment_id=payment.id, payment_type=payment.payment_type)
    except Exception:
        pass
