from datetime import date

from flask import current_app, flash, redirect, session, url_for

from app import db
from app.models import Credit, Membership, Payment, User
from app.services.settings_service import SettingsService
from app.services.sumup_service import SumUpService
from app.utils.session import clear_session_keys


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


class PaymentProcessingService:
    @staticmethod
    def _finalize_and_redirect(user, payment, clear_keys, flash_message, flash_category, redirect_endpoint, redirect_kwargs=None, send_receipt=True):
        """Helper to send/queue receipt, clear session keys, flash a message and return a redirect response.

        - clear_keys: iterable of session key names to clear
        - flash_message: message string to flash
        - flash_category: category for flash (e.g., 'success')
        - redirect_endpoint: endpoint name for url_for
        - redirect_kwargs: optional dict of kwargs passed to url_for
        """
        if send_receipt:
            try:
                # Send or queue the payment receipt
                PaymentProcessingService.send_payment_receipt(user.id, payment.id)
            except Exception as e:
                current_app.logger.error(f"Failed to hand off receipt email to MailService: {str(e)}")

        # Clear session keys
        if clear_keys:
            clear_session_keys(*clear_keys)

        # Flash and redirect
        if flash_message:
            flash(flash_message, flash_category)

        if redirect_kwargs is None:
            redirect_kwargs = {}

        return redirect(url_for(redirect_endpoint, **redirect_kwargs))

    @staticmethod
    def send_payment_receipt(user_id, payment_id):
        """Send payment receipt email synchronously."""
        from app.services.mail_service import send_payment_receipt

        send_payment_receipt(user_id, payment_id)

    @staticmethod
    def validate_card_details(card_number, card_name, expiry_month, expiry_year, cvv):
        return all([card_number, card_name, expiry_month, expiry_year, cvv])

    @staticmethod
    def handle_signup_payment(user_id, checkout_id, result):
        payment_id = session.get("signup_payment_id")
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_code") or result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id, processor="sumup")
        if user.membership:
            user.membership.activate()
        db.session.commit()

        return PaymentProcessingService._finalize_and_redirect(
            user,
            payment,
            clear_keys=("signup_user_id", "signup_payment_id", "checkout_amount", "checkout_description"),
            flash_message="Payment successful! Your membership is now active. A receipt has been sent to your email.",
            flash_category="success",
            redirect_endpoint="auth.login",
        )

    @staticmethod
    def handle_membership_renewal(user_id, checkout_id, result):
        payment_id = session.get("membership_renewal_payment_id")
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_code") or result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id, processor="sumup")

        # Renew or create membership
        if user.membership:
            user.membership.renew()
        else:
            start_date = date.today()
            membership = Membership(
                user_id=user.id,
                start_date=start_date,
                expiry_date=SettingsService.calculate_membership_expiry(start_date).date(),
                status="active",
            )
            db.session.add(membership)

        db.session.commit()

        return PaymentProcessingService._finalize_and_redirect(
            user,
            payment,
            clear_keys=("membership_renewal_user_id", "membership_renewal_payment_id", "checkout_amount", "checkout_description"),
            flash_message="Membership renewed successfully! A receipt has been sent to your email.",
            flash_category="success",
            redirect_endpoint="member.dashboard",
        )

    @staticmethod
    def handle_credit_purchase(user_id, checkout_id, result):
        payment_id = session.get("credit_purchase_payment_id")
        quantity = session.get("credit_purchase_quantity", 1)
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_code") or result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id, processor="sumup")

        # Add credits to membership
        if user.membership:
            user.membership.add_credits(quantity)

        # Record the credit purchase
        credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
        db.session.add(credit)
        db.session.commit()

        # Send credit purchase receipt
        try:
            from app.services.mail_service import send_credit_purchase_receipt

            send_credit_purchase_receipt(user_id, payment.id, quantity)
        except Exception as e:
            current_app.logger.error(f"Failed to send credit purchase receipt: {str(e)}")

        return PaymentProcessingService._finalize_and_redirect(
            user,
            payment,
            clear_keys=("credit_purchase_user_id", "credit_purchase_payment_id", "credit_purchase_quantity", "checkout_amount", "checkout_description"),
            flash_message=f"Successfully purchased {quantity} credits! A receipt has been sent to your email.",
            flash_category="success",
            redirect_endpoint="member.dashboard",
            send_receipt=False,  # We're sending a custom credit receipt above
        )

    @staticmethod
    def handle_payment_failure(checkout_id, result):
        status = result.get("status", "UNKNOWN")
        error_msg = result.get("error", "Payment was not approved")

        if status == "FAILED":
            flash(f"Payment declined: {error_msg}", "error")
        elif status == "PENDING":
            flash(
                "Payment is pending. Please contact us if the issue persists.",
                "warning",
            )
        else:
            flash(f"Payment failed: {error_msg}", "error")

        return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))
