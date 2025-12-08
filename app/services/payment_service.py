from datetime import date, timedelta

from flask import current_app, flash, redirect, session, url_for

from app import db, task_queue
from app.models import Credit, Membership, Payment, User
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


class PaymentProcessingService:

    @staticmethod
    def queue_payment_receipt(user_id, payment_id):
        if task_queue:
            from app.services.background_jobs import send_payment_receipt_job

            try:
                task_queue.enqueue(send_payment_receipt_job, user_id, payment_id)
                current_app.logger.info(f"Queued payment receipt email for user {user_id}, payment {payment_id}")
            except Exception as e:
                current_app.logger.error(f"Failed to queue receipt email: {str(e)}")
        else:
            from app.utils.email import send_payment_receipt

            try:
                user = db.session.get(User, user_id)
                payment = db.session.get(Payment, payment_id)
                if user and payment:
                    send_payment_receipt(user, payment, user.membership)
            except Exception as e:
                current_app.logger.error(f"Failed to send receipt email: {str(e)}")

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

        PaymentProcessingService.queue_payment_receipt(user.id, payment.id)

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
            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                status="active",
            )
            db.session.add(membership)

        db.session.commit()

        # Queue payment receipt email as background job
        PaymentProcessingService.queue_payment_receipt(user.id, payment.id)

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
        payment_id = session.get("credit_purchase_payment_id")
        quantity = session.get("credit_purchase_quantity", 1)
        payment = db.session.get(Payment, payment_id)
        user = db.session.get(User, user_id)

        if not payment or not user:
            return None

        transaction_id = result.get("transaction_code") or result.get("transaction_id") or checkout_id
        payment.mark_completed(transaction_id, processor="sumup")

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
