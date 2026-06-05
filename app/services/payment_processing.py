from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.settings import calculate_membership_expiry
from app.events import credit_purchased, payment_completed
from app.models.credit import Credit
from app.models.membership import Membership
from app.models.payment import Payment
from app.services import users as user_service
from app.services.result import ServiceResult

logger = logging.getLogger(__name__)


def handle_signup_payment(db: Session, user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
    payment = db.get(Payment, payment_id)
    user = user_service.get_user_by_id(db, user_id)
    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.")

    try:
        payment.mark_completed(transaction_id, processor="sumup")
        if user.membership:
            user.membership.activate()
    except Exception:
        logger.exception("Signup payment processing failed")
        return ServiceResult.fail("Payment could not be processed. Please try again.")

    try:
        payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
    except Exception:
        logger.exception("Failed to emit payment_completed event")

    return ServiceResult.ok(message="Payment successful! Your membership is now active. A receipt has been sent to your email.")


def handle_membership_renewal(db: Session, user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
    payment = db.get(Payment, payment_id)
    user = user_service.get_user_by_id(db, user_id)
    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.")

    try:
        payment.mark_completed(transaction_id, processor="sumup")
        if user.membership:
            expiry_date = calculate_membership_expiry(db, date.today()).date()
            user.membership.renew(expiry_date=expiry_date)
        else:
            start_date = date.today()
            membership = Membership(
                user_id=user.id,
                start_date=start_date,
                expiry_date=calculate_membership_expiry(db, start_date).date(),
                status="active",
            )
            db.add(membership)
    except Exception:
        logger.exception("Membership renewal processing failed")
        return ServiceResult.fail("Renewal could not be processed. Please try again.")

    try:
        payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
    except Exception:
        logger.exception("Failed to emit payment_completed event")

    return ServiceResult.ok(message="Membership renewed successfully! A receipt has been sent to your email.")


def handle_credit_purchase(
    db: Session,
    user_id: int,
    payment_id: int,
    quantity: int,
    transaction_id: str,
) -> ServiceResult[None]:
    payment = db.get(Payment, payment_id)
    user = user_service.get_user_by_id(db, user_id)
    if not payment or not user:
        return ServiceResult.fail("Payment or user not found.")

    try:
        payment.mark_completed(transaction_id, processor="sumup")
        if user.membership:
            user.membership.add_credits(quantity)
        credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
        db.add(credit)
    except Exception:
        logger.exception("Credit purchase processing failed")
        return ServiceResult.fail("Credit purchase could not be processed. Please try again.")

    try:
        credit_purchased.send(user_id=user_id, payment_id=payment.id, quantity=quantity)
    except Exception:
        logger.exception("Failed to emit credit_purchased event")

    return ServiceResult.ok(message=f"Successfully purchased {quantity} credits! A receipt has been sent to your email.")
