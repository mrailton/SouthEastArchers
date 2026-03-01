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
from app.utils.session import get_user_id_from_session

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
            return PaymentProcessingService.handle_payment_failure(
                checkout_id,
                {
                    "success": False,
                    "status": status or "FAILED",
                    "error": "Payment was not approved",
                },
            )

        result = {
            "success": True,
            "status": "PAID",
            "transaction_code": transaction_code,
            "transaction_id": transaction_id,
        }

        user_id = get_user_id_from_session(current_user)

        if user_id is None:
            flash("User session not found. Please try again.", "error")
            return redirect(url_for("auth.login"))

        if session.get("signup_user_id"):
            return PaymentProcessingService.handle_signup_payment(user_id, checkout_id, result)

        if session.get("membership_renewal_user_id"):
            return PaymentProcessingService.handle_membership_renewal(user_id, checkout_id, result)

        if session.get("credit_purchase_user_id"):
            return PaymentProcessingService.handle_credit_purchase(user_id, checkout_id, result)

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
    payments = PaymentRepository.get_by_user(user.id)

    return render_template("payment/history.html", payments=payments)


@bp.post("/membership/cash")
@login_required
def membership_cash_payment():
    """Handle cash membership payment initiation"""
    payment_service = PaymentService()
    result = payment_service.initiate_cash_membership_payment(current_user)

    if result.get("success"):
        return render_template(
            "payment/cash_pending.html",
            payment_type="membership",
            amount=result["amount"],
            instructions=result["instructions"],
        )
    else:
        flash(result.get("error", "Error creating payment."), "error")
        return redirect(url_for("payment.membership_payment"))


@bp.post("/credits/cash")
@login_required
def credits_cash_payment():
    """Handle cash credits purchase initiation"""
    quantity = int(request.form.get("quantity", 1))
    payment_service = PaymentService()
    result = payment_service.initiate_cash_credit_purchase(current_user, quantity)

    if result.get("success"):
        return render_template(
            "payment/cash_pending.html",
            payment_type="credits",
            amount=result["amount"],
            quantity=result["quantity"],
            instructions=result["instructions"],
        )
    else:
        flash(result.get("error", "Error creating payment."), "error")
        return redirect(url_for("payment.credits"))
