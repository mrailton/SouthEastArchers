from flask import current_app, flash, redirect, session, url_for
from flask_login import current_user, login_required

from app.services import PaymentProcessingService, SumUpService
from app.utils import clear_session_keys, get_user_id_from_session


class CompleteCheckoutController:
    def __init__(self):
        super().__init__()
        self.sumup_service = SumUpService
        self.payment_processing_service = PaymentProcessingService

    @login_required
    def __call__(self, checkout_id):
        try:
            sumup = self.sumup_service()
            checkout = sumup.get_checkout(checkout_id)

            if not checkout:
                flash("Could not verify payment status. Please contact us.", "error")
                return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))

            status = getattr(checkout, "status", None)
            transaction_code = getattr(checkout, "transaction_code", None)
            transaction_id = getattr(checkout, "transaction_id", None)

            if status != "PAID":
                if status == "FAILED":
                    flash("Payment declined: Payment was not approved", "error")
                elif status == "PENDING":
                    flash("Payment is pending. Please contact us if the issue persists.", "warning")
                else:
                    flash("Payment failed: Payment was not approved", "error")
                return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))

            txn_id = transaction_code or transaction_id or checkout_id
            user_id = get_user_id_from_session(current_user)

            if user_id is None:
                flash("User session not found. Please try again.", "error")
                return redirect(url_for("auth.login"))

            signup_payment_id = session.get("signup_payment_id")
            if session.get("signup_user_id") and signup_payment_id:
                result = self.payment_processing_service.handle_signup_payment(user_id, signup_payment_id, txn_id)
                clear_session_keys("signup_user_id", "signup_payment_id", "checkout_amount", "checkout_description")
                flash(result.message, "success" if result.success else "error")
                return redirect(url_for("auth.login"))

            renewal_payment_id = session.get("membership_renewal_payment_id")
            if session.get("membership_renewal_user_id") and renewal_payment_id:
                result = self.payment_processing_service.handle_membership_renewal(user_id, renewal_payment_id, txn_id)
                clear_session_keys("membership_renewal_user_id", "membership_renewal_payment_id", "checkout_amount", "checkout_description")
                flash(result.message, "success" if result.success else "error")
                return redirect(url_for("member.dashboard"))

            credit_payment_id = session.get("credit_purchase_payment_id")
            if session.get("credit_purchase_user_id") and credit_payment_id:
                quantity = session.get("credit_purchase_quantity", 1)
                result = self.payment_processing_service.handle_credit_purchase(user_id, credit_payment_id, quantity, txn_id)
                clear_session_keys(
                    "credit_purchase_user_id", "credit_purchase_payment_id", "credit_purchase_quantity", "checkout_amount", "checkout_description"
                )
                flash(result.message, "success" if result.success else "error")
                return redirect(url_for("member.dashboard"))

            flash("Payment processed successfully!", "success")
            return redirect(url_for("member.dashboard") if current_user.is_authenticated else url_for("auth.login"))

        except Exception as e:
            current_app.logger.error(f"Error completing checkout: {str(e)}")
            flash("An error occurred processing your payment. Please try again.", "error")
            return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))
