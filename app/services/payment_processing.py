from __future__ import annotations

import logging
from datetime import date

from app.events import credit_purchased, payment_completed
from app.models import Credit, Membership
from app.repositories import BaseRepository, CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services import settings
from app.services.result import ServiceResult

logger = logging.getLogger(__name__)


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
