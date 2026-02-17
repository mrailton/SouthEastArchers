from flask import current_app, session

from app import db
from app.models import Payment, User
from app.services.settings_service import SettingsService
from app.services.sumup_service import SumUpService


class PaymentService:
    def __init__(self):
        self.processor = SumUpService()

    def create_checkout(self, amount_cents, description):
        return self.processor.create_checkout(
            amount=amount_cents,
            currency="EUR",
            description=description,
            checkout_reference=None,  # Can be added if needed
        )

    def process_payment(self, checkout_id, card_number, card_name, expiry_month, expiry_year, cvv):
        return self.processor.process_checkout_payment(
            checkout_id=checkout_id,
            card_number=card_number,
            card_name=card_name,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
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
        db.session.add(payment)
        db.session.commit()

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
            db.session.delete(payment)
            db.session.commit()
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
        db.session.add(payment)
        db.session.commit()

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
            db.session.delete(payment)
            db.session.commit()
            return {"success": False, "error": "Error creating payment. Please try again."}

    def initiate_cash_membership_payment(self, user: User) -> dict:
        """Create pending cash payment record for membership.

        The payment will remain pending until approved by an admin.
        """
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
        db.session.add(payment)
        db.session.commit()

        # Send confirmation email
        try:
            from app.services.mail_service import send_cash_payment_pending_email

            send_cash_payment_pending_email(user.id, payment.id)
        except Exception as e:
            current_app.logger.error(f"Failed to send cash payment pending email: {e}")

        return {
            "success": True,
            "payment_id": payment.id,
            "amount": amount_cents / 100.0,
            "instructions": settings.cash_payment_instructions,
        }

    def initiate_cash_credit_purchase(self, user: User, quantity: int) -> dict:
        """Create pending cash payment record for credit purchase.

        The payment will remain pending until approved by an admin.
        """
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
        db.session.add(payment)
        db.session.commit()

        # Send confirmation email
        try:
            from app.services.mail_service import send_cash_payment_pending_email

            send_cash_payment_pending_email(user.id, payment.id)
        except Exception as e:
            current_app.logger.error(f"Failed to send cash payment pending email: {e}")

        return {
            "success": True,
            "payment_id": payment.id,
            "quantity": quantity,
            "amount": amount_cents / 100.0,
            "instructions": settings.cash_payment_instructions,
        }
