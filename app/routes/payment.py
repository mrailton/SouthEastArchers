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

from app.models import Payment
from app.services import PaymentProcessingService, PaymentService
from app.utils.session import get_user_id_from_session

bp = Blueprint("payment", __name__, url_prefix="/payment")


@bp.get("/checkout/<checkout_id>")
def show_checkout(checkout_id):
    amount = session.get("checkout_amount", 100.00)
    description = session.get("checkout_description", "Payment")

    return render_template(
        "payment/checkout.html",
        checkout_id=checkout_id,
        amount=amount,
        description=description,
    )


@bp.post("/checkout/<checkout_id>/process")
def process_checkout(checkout_id):
    try:
        card_number = request.form.get("card_number", "").replace(" ", "")
        card_name = request.form.get("card_name", "")
        expiry_month = request.form.get("expiry_month", "")
        expiry_year = request.form.get("expiry_year", "")
        cvv = request.form.get("cvv", "")

        if not PaymentProcessingService.validate_card_details(card_number, card_name, expiry_month, expiry_year, cvv):
            flash("Please fill in all card details", "error")
            return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))

        payment_service = PaymentService()
        result = payment_service.process_payment(
            checkout_id=checkout_id,
            card_number=card_number,
            card_name=card_name,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
        )

        if not result.get("success"):
            return PaymentProcessingService.handle_payment_failure(
                checkout_id,
                {
                    "success": False,
                    "status": result.get("status", "FAILED"),
                    "error": result.get("error", "Payment was not approved"),
                },
            )

        user_id = get_user_id_from_session(current_user)

        if session.get("signup_user_id"):
            return PaymentProcessingService.handle_signup_payment(user_id, checkout_id, result)

        if session.get("membership_renewal_user_id"):
            return PaymentProcessingService.handle_membership_renewal(user_id, checkout_id, result)

        if session.get("credit_purchase_user_id"):
            return PaymentProcessingService.handle_credit_purchase(user_id, checkout_id, result)

        flash("Payment processed successfully!", "success")
        return redirect(url_for("member.dashboard") if current_user.is_authenticated else url_for("auth.login"))

    except Exception as e:
        current_app.logger.error(f"Error processing checkout: {str(e)}")
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

    if result.get("success"):
        return redirect(url_for("payment.show_checkout", checkout_id=result["checkout_id"]))
    else:
        flash(result.get("error", "Error creating payment."), "error")

    return render_template("payment/membership.html")


@bp.get("/credits")
@login_required
def credits():
    """Display credits purchase page"""
    return render_template("payment/credits.html")


@bp.post("/credits")
@login_required
def credits_post():
    """Handle credits purchase initiation"""
    quantity = int(request.form.get("quantity", 1))
    payment_service = PaymentService()
    result = payment_service.initiate_credit_purchase(current_user, quantity)

    if result.get("success"):
        return redirect(url_for("payment.show_checkout", checkout_id=result["checkout_id"]))
    else:
        flash(result.get("error", "Error creating payment."), "error")

    return render_template("payment/credits.html")


@bp.get("/history")
@login_required
def history():
    user = current_user
    payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()

    return render_template("payment/history.html", payments=payments)
