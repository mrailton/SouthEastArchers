from flask import current_app, flash, redirect, session, url_for

from app import db
from app.models import Payment, User
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


