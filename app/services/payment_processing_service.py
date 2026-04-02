from datetime import date

from flask import current_app

from app.events import credit_purchased, payment_completed
from app.models import Credit, Membership
from app.repositories import CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services.result import ServiceResult
from app.services.settings_service import SettingsService


class PaymentProcessingService:
    @staticmethod
    def handle_signup_payment(user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
        """Process a successful signup payment.

        Marks the payment as completed and activates the user's membership.
        """
        payment = PaymentRepository.get_by_id(payment_id)
        user = UserRepository.get_by_id(user_id)

        if not payment or not user:
            return ServiceResult.fail("Payment or user not found.")

        payment.mark_completed(transaction_id, processor="sumup")
        if user.membership:
            user.membership.activate()
        UserRepository.save()

        try:
            payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
        except Exception as e:
            current_app.logger.error(f"Failed to emit payment_completed event: {str(e)}")

        return ServiceResult.ok(message="Payment successful! Your membership is now active. A receipt has been sent to your email.")

    @staticmethod
    def handle_membership_renewal(user_id: int, payment_id: int, transaction_id: str) -> ServiceResult[None]:
        """Process a successful membership renewal payment.

        Marks the payment as completed and renews (or creates) the membership.
        """
        payment = PaymentRepository.get_by_id(payment_id)
        user = UserRepository.get_by_id(user_id)

        if not payment or not user:
            return ServiceResult.fail("Payment or user not found.")

        payment.mark_completed(transaction_id, processor="sumup")

        if user.membership:
            expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
            user.membership.renew(expiry_date=expiry_date)
        else:
            start_date = date.today()
            membership = Membership(
                user_id=user.id,
                start_date=start_date,
                expiry_date=SettingsService.calculate_membership_expiry(start_date).date(),
                status="active",
            )
            MembershipRepository.add(membership)

        UserRepository.save()

        try:
            payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
        except Exception as e:
            current_app.logger.error(f"Failed to emit payment_completed event: {str(e)}")

        return ServiceResult.ok(message="Membership renewed successfully! A receipt has been sent to your email.")

    @staticmethod
    def handle_credit_purchase(user_id: int, payment_id: int, quantity: int, transaction_id: str) -> ServiceResult[None]:
        """Process a successful credit purchase payment.

        Marks the payment as completed, adds credits to the membership,
        and records the credit purchase.
        """
        payment = PaymentRepository.get_by_id(payment_id)
        user = UserRepository.get_by_id(user_id)

        if not payment or not user:
            return ServiceResult.fail("Payment or user not found.")

        payment.mark_completed(transaction_id, processor="sumup")

        if user.membership:
            user.membership.add_credits(quantity)

        credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
        CreditRepository.add(credit)
        CreditRepository.save()

        try:
            credit_purchased.send(user_id=user_id, payment_id=payment.id, quantity=quantity)
        except Exception as e:
            current_app.logger.error(f"Failed to emit credit_purchased event: {str(e)}")

        return ServiceResult.ok(message=f"Successfully purchased {quantity} credits! A receipt has been sent to your email.")
