"""Payment processing service for handling various payment types"""

from datetime import date, timedelta

from flask import current_app, flash, redirect, session, url_for

from app import db
from app.models import Credit, Membership, Payment, User
from app.utils.email import send_payment_receipt
from app.utils.session import clear_session_keys


class PaymentProcessingService:
    """Service for processing different types of payments"""

    @staticmethod
    def validate_card_details(card_number, card_name, expiry_month, expiry_year, cvv):
        """Validate card details are present"""
        return all([card_number, card_name, expiry_month, expiry_year, cvv])

    @staticmethod
    def handle_signup_payment(user_id, checkout_id, result):
        """Handle signup payment processing"""
        payment_id = session.get("signup_payment_id")
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id)
        if user.membership:
            user.membership.activate()
        db.session.commit()

        # Send payment receipt email
        try:
            send_payment_receipt(user, payment, user.membership)
        except Exception as e:
            current_app.logger.error(f"Failed to send receipt email: {str(e)}")

        clear_session_keys(
            "signup_user_id",
            "signup_payment_id",
            "checkout_amount",
            "checkout_description",
        )

        flash(
            "Payment successful! Your membership is now active. A receipt has been sent to your email.",
            "success",
        )
        return redirect(url_for("auth.login"))

    @staticmethod
    def handle_membership_renewal(user_id, checkout_id, result):
        """Handle membership renewal payment processing"""
        payment_id = session.get("membership_renewal_payment_id")
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id)

        # Renew or create membership
        if user.membership:
            user.membership.renew()
        else:
            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                status="active",
            )
            db.session.add(membership)

        db.session.commit()

        # Send payment receipt
        try:
            send_payment_receipt(user, payment, user.membership)
        except Exception as e:
            current_app.logger.error(f"Failed to send receipt email: {str(e)}")

        clear_session_keys(
            "membership_renewal_user_id",
            "membership_renewal_payment_id",
            "checkout_amount",
            "checkout_description",
        )

        flash(
            "Membership renewed successfully! A receipt has been sent to your email.",
            "success",
        )
        return redirect(url_for("member.dashboard"))

    @staticmethod
    def handle_credit_purchase(user_id, checkout_id, result):
        """Handle credit purchase payment processing"""
        payment_id = session.get("credit_purchase_payment_id")
        quantity = session.get("credit_purchase_quantity", 1)
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id)

        # Add credits
        credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
        db.session.add(credit)
        db.session.commit()

        clear_session_keys(
            "credit_purchase_user_id",
            "credit_purchase_payment_id",
            "credit_purchase_quantity",
            "checkout_amount",
            "checkout_description",
        )

        flash(f"Successfully purchased {quantity} credits!", "success")
        return redirect(url_for("member.dashboard"))

    @staticmethod
    def handle_payment_failure(checkout_id, result):
        """Handle payment failure or pending status"""
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
