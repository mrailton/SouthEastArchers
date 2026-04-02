from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required

from app.repositories import PaymentRepository
from app.services import PaymentProcessingService, PaymentService
from app.services.sumup_service import SumUpService
from app.utils.session import clear_session_keys, get_user_id_from_session

bp = Blueprint("payment", __name__, url_prefix="/payment")


@bp.get("/checkout/<checkout_id>")
@login_required
def show_checkout(checkout_id):
    amount = session.get("checkout_amount", 100.00)
    description = session.get("checkout_description", "Payment")

    return render_template(
        "payment/checkout.html",
        checkout_id=checkout_id,
        amount=amount,
        description=description,
    )


@bp.post("/checkout/<checkout_id>/complete")
@login_required
def complete_checkout(checkout_id):
    """Verify payment completion after SumUp Card Widget processes the payment."""
    try:
        sumup = SumUpService()
        checkout = sumup.get_checkout(checkout_id)

        if not checkout:
            flash("Could not verify payment status. Please contact us.", "error")
            return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))

        status = getattr(checkout, "status", None)
        transaction_code = getattr(checkout, "transaction_code", None)
        transaction_id = getattr(checkout, "transaction_id", None)

        if status != "PAID":
            # Handle payment failure inline
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

        # --- Signup payment flow ---
        signup_payment_id = session.get("signup_payment_id")
        if session.get("signup_user_id") and signup_payment_id:
            result = PaymentProcessingService.handle_signup_payment(user_id, signup_payment_id, txn_id)
            clear_session_keys("signup_user_id", "signup_payment_id", "checkout_amount", "checkout_description")
            flash(result.message, "success" if result.success else "error")
            return redirect(url_for("auth.login"))

        # --- Membership renewal flow ---
        renewal_payment_id = session.get("membership_renewal_payment_id")
        if session.get("membership_renewal_user_id") and renewal_payment_id:
            result = PaymentProcessingService.handle_membership_renewal(user_id, renewal_payment_id, txn_id)
            clear_session_keys("membership_renewal_user_id", "membership_renewal_payment_id", "checkout_amount", "checkout_description")
            flash(result.message, "success" if result.success else "error")
            return redirect(url_for("member.dashboard"))

        # --- Credit purchase flow ---
        credit_payment_id = session.get("credit_purchase_payment_id")
        if session.get("credit_purchase_user_id") and credit_payment_id:
            quantity = session.get("credit_purchase_quantity", 1)
            result = PaymentProcessingService.handle_credit_purchase(user_id, credit_payment_id, quantity, txn_id)
            clear_session_keys("credit_purchase_user_id", "credit_purchase_payment_id", "credit_purchase_quantity", "checkout_amount", "checkout_description")
            flash(result.message, "success" if result.success else "error")
            return redirect(url_for("member.dashboard"))

        flash("Payment processed successfully!", "success")
        return redirect(url_for("member.dashboard") if current_user.is_authenticated else url_for("auth.login"))

    except Exception as e:
        current_app.logger.error(f"Error completing checkout: {str(e)}")
        flash("An error occurred processing your payment. Please try again.", "error")
        return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))


@bp.get("/membership")
@login_required
def membership_payment():
    """Display membership payment page"""
    return render_template("payment/membership.html")


@bp.post("/membership")
@login_required
def membership_payment_post():
    """Handle membership payment initiation"""
    payment_service = PaymentService()
    result = payment_service.initiate_membership_payment(current_user)

    if result.success:
        data = result.data
        session["membership_renewal_user_id"] = data["user_id"]
        session["membership_renewal_payment_id"] = data["payment_id"]
        session["checkout_amount"] = data["amount"]
        session["checkout_description"] = data["description"]
        return redirect(url_for("payment.show_checkout", checkout_id=data["checkout_id"]))
    else:
        flash(result.message, "error")

    return render_template("payment/membership.html")


@bp.get("/credits")
@login_required
def credits():
    if not current_user.membership:
        flash("You must have an active membership to purchase credits.", "error")
        return redirect(url_for("payment.membership_payment"))

    return render_template("payment/credits.html")


MAX_CREDIT_QUANTITY = 50


# ...existing code...


@bp.post("/credits")
@login_required
def credits_post():
    """Handle credits purchase initiation"""
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError, TypeError:
        flash("Invalid quantity.", "error")
        return render_template("payment/credits.html")

    if quantity < 1 or quantity > MAX_CREDIT_QUANTITY:
        flash(f"Quantity must be between 1 and {MAX_CREDIT_QUANTITY}.", "error")
        return render_template("payment/credits.html")

    payment_service = PaymentService()
    result = payment_service.initiate_credit_purchase(current_user, quantity)

    if result.success:
        data = result.data
        session["credit_purchase_user_id"] = data["user_id"]
        session["credit_purchase_payment_id"] = data["payment_id"]
        session["credit_purchase_quantity"] = data["quantity"]
        session["checkout_amount"] = data["amount"]
        session["checkout_description"] = data["description"]
        return redirect(url_for("payment.show_checkout", checkout_id=data["checkout_id"]))
    else:
        flash(result.message, "error")

    return render_template("payment/credits.html")


@bp.get("/history")
@login_required
def history():
    user = current_user
    payments = PaymentRepository.get_by_user(user.id)

    return render_template("payment/history.html", payments=payments)


@bp.post("/membership/cash")
@login_required
def membership_cash_payment():
    """Handle cash membership payment initiation"""
    payment_service = PaymentService()
    result = payment_service.initiate_cash_membership_payment(current_user)

    if result.success:
        data = result.data
        return render_template(
            "payment/cash_pending.html",
            payment_type="membership",
            amount=data["amount"],
            instructions=data["instructions"],
        )
    else:
        flash(result.message, "error")
        return redirect(url_for("payment.membership_payment"))


@bp.post("/credits/cash")
@login_required
def credits_cash_payment():
    """Handle cash credits purchase initiation"""
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError, TypeError:
        flash("Invalid quantity.", "error")
        return redirect(url_for("payment.credits"))

    if quantity < 1 or quantity > MAX_CREDIT_QUANTITY:
        flash(f"Quantity must be between 1 and {MAX_CREDIT_QUANTITY}.", "error")
        return redirect(url_for("payment.credits"))

    payment_service = PaymentService()
    result = payment_service.initiate_cash_credit_purchase(current_user, quantity)

    if result.success:
        data = result.data
        return render_template(
            "payment/cash_pending.html",
            payment_type="credits",
            amount=data["amount"],
            quantity=data["quantity"],
            instructions=data["instructions"],
        )
    else:
        flash(result.message, "error")
        return redirect(url_for("payment.credits"))
