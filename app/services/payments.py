from __future__ import annotations

import logging
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import get_setting
from app.enums import PaymentMethod, PaymentType
from app.events import cash_payment_submitted
from app.models.payment import Payment
from app.models.user import User
from app.services.result import ServiceResult
from app.services.sumup import SumUpService

logger = logging.getLogger(__name__)
MAX_CREDIT_QUANTITY = 50


class CheckoutProcessor(Protocol):
    def create_checkout(self, amount: int, currency: str = "EUR", description: str = "") -> dict[str, Any] | None: ...


def get_user_payments(db: Session, user_id: int) -> list[Payment]:
    return list(
        db.scalars(
            select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
        ).all()
    )


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
