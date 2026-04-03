from typing import Any

from flask import current_app

from app.enums import PaymentMethod, PaymentType
from app.events import cash_payment_submitted
from app.models import Payment, User
from app.repositories import PaymentRepository
from app.services.result import ServiceResult
from app.services.settings_service import SettingsService
from app.services.sumup_service import SumUpService


class PaymentService:
    def __init__(self, processor: Any = None) -> None:
        self.processor = processor or SumUpService()

    def create_checkout(self, amount_cents: int, description: str) -> dict[str, Any] | None:
        return self.processor.create_checkout(
            amount=amount_cents,
            currency="EUR",
            description=description,
        )

    def initiate_membership_payment(self, user: User) -> ServiceResult[dict]:
        """Create payment record and SumUp checkout for membership renewal.

        On success, ``result.data`` contains::

            {"checkout_id": str, "payment_id": int, "amount": float, "description": str}
        """
        amount_cents: int = SettingsService.get("annual_membership_cost")
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
        PaymentRepository.add(payment)
        PaymentRepository.save()

        checkout = self.create_checkout(amount_cents=amount_cents, description=description)

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
        else:
            PaymentRepository.delete(payment)
            PaymentRepository.save()
            return ServiceResult.fail("Error creating payment. Please try again.")

    def initiate_credit_purchase(self, user: User, quantity: int) -> ServiceResult[dict]:
        """Create payment record and SumUp checkout for credit purchase.

        On success, ``result.data`` contains::

            {"checkout_id": str, "payment_id": int, "user_id": int, "quantity": int, "amount": float, "description": str}
        """
        amount_cents: int = quantity * SettingsService.get("additional_shoot_cost")
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
        PaymentRepository.add(payment)
        PaymentRepository.save()

        checkout = self.create_checkout(amount_cents=amount_cents, description=description)

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
        else:
            PaymentRepository.delete(payment)
            PaymentRepository.save()
            return ServiceResult.fail("Error creating payment. Please try again.")

    @staticmethod
    def initiate_cash_membership_payment(user: User) -> ServiceResult[dict]:
        """Create pending cash payment record for membership.

        On success, ``result.data`` contains::

            {"payment_id": int, "amount": float, "instructions": str}
        """
        amount_cents: int = SettingsService.get("annual_membership_cost")

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type=PaymentType.MEMBERSHIP,
            payment_method=PaymentMethod.CASH,
            description=f"Annual Membership (Cash) - {user.name}",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        # Emit event — handler sends confirmation email
        try:
            cash_payment_submitted.send(user_id=user.id, payment_id=payment.id)
        except Exception as e:
            current_app.logger.error(f"Failed to emit cash_payment_submitted event: {e}")

        return ServiceResult.ok(
            data={
                "payment_id": payment.id,
                "amount": amount_cents / 100.0,
                "instructions": SettingsService.get("cash_payment_instructions"),
            }
        )

    @staticmethod
    def initiate_cash_credit_purchase(user: User, quantity: int) -> ServiceResult[dict]:
        """Create pending cash payment record for credit purchase.

        On success, ``result.data`` contains::

            {"payment_id": int, "quantity": int, "amount": float, "instructions": str}
        """
        amount_cents: int = quantity * SettingsService.get("additional_shoot_cost")

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type=PaymentType.CREDITS,
            payment_method=PaymentMethod.CASH,
            description=f"{quantity} shooting credits (Cash)",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        # Emit event — handler sends confirmation email
        try:
            cash_payment_submitted.send(user_id=user.id, payment_id=payment.id)
        except Exception as e:
            current_app.logger.error(f"Failed to emit cash_payment_submitted event: {e}")

        return ServiceResult.ok(
            data={
                "payment_id": payment.id,
                "quantity": quantity,
                "amount": amount_cents / 100.0,
                "instructions": SettingsService.get("cash_payment_instructions"),
            }
        )
