from typing import Any

from flask import current_app, session

from app.events import cash_payment_submitted
from app.models import Payment, User
from app.repositories import PaymentRepository
from app.services.settings_service import SettingsService
from app.services.sumup_service import SumUpService


class PaymentService:
    def __init__(self) -> None:
        self.processor = SumUpService()

    def create_checkout(self, amount_cents: int, description: str) -> dict[str, Any] | None:
        return self.processor.create_checkout(
            amount=amount_cents,
            currency="EUR",
            description=description,
        )

    def initiate_membership_payment(self, user: User) -> dict:
        """Create payment record and checkout for membership renewal."""
        amount_cents = current_app.config["ANNUAL_MEMBERSHIP_COST"]

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            description=f"Annual Membership - {user.name}",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        checkout = self.create_checkout(
            amount_cents=amount_cents,
            description=f"Annual Membership - {user.name}",
        )

        if checkout:
            session["membership_renewal_user_id"] = user.id
            session["membership_renewal_payment_id"] = payment.id
            session["checkout_amount"] = float(amount_cents / 100.0)
            session["checkout_description"] = f"Annual Membership - {user.name}"
            return {"success": True, "checkout_id": checkout.get("id")}
        else:
            PaymentRepository.delete(payment)
            PaymentRepository.save()
            return {"success": False, "error": "Error creating payment. Please try again."}

    def initiate_credit_purchase(self, user: User, quantity: int) -> dict:
        """Create payment record and checkout for credit purchase."""
        amount_cents = quantity * current_app.config["ADDITIONAL_NIGHT_COST"]

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type="credits",
            payment_method="online",
            description=f"{quantity} shooting credits",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        checkout = self.create_checkout(
            amount_cents=amount_cents,
            description=f"{quantity} credits - {user.name}",
        )

        if checkout:
            session["credit_purchase_user_id"] = user.id
            session["credit_purchase_payment_id"] = payment.id
            session["credit_purchase_quantity"] = quantity
            session["checkout_amount"] = float(amount_cents / 100.0)
            session["checkout_description"] = f"{quantity} credits - {user.name}"
            return {"success": True, "checkout_id": checkout.get("id")}
        else:
            PaymentRepository.delete(payment)
            PaymentRepository.save()
            return {"success": False, "error": "Error creating payment. Please try again."}

    def initiate_cash_membership_payment(self, user: User) -> dict:
        """Create pending cash payment record for membership."""
        settings = SettingsService.get()
        amount_cents = settings.annual_membership_cost

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type="membership",
            payment_method="cash",
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

        return {
            "success": True,
            "payment_id": payment.id,
            "amount": amount_cents / 100.0,
            "instructions": settings.cash_payment_instructions,
        }

    def initiate_cash_credit_purchase(self, user: User, quantity: int) -> dict:
        """Create pending cash payment record for credit purchase."""
        settings = SettingsService.get()
        amount_cents = quantity * settings.additional_shoot_cost

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type="credits",
            payment_method="cash",
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

        return {
            "success": True,
            "payment_id": payment.id,
            "quantity": quantity,
            "amount": amount_cents / 100.0,
            "instructions": settings.cash_payment_instructions,
        }
