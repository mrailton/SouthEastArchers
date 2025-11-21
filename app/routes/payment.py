from datetime import date, timedelta

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

from app import db
from app.models import Credit, Membership, Payment, User
from app.services import PaymentProcessingService, SumUpService
from app.utils.email import send_payment_receipt
from app.utils.session import get_user_id_from_session

bp = Blueprint("payment", __name__, url_prefix="/payment")


@bp.route("/checkout/<checkout_id>")
def show_checkout(checkout_id):
    """Display payment form for a checkout"""
    from flask_wtf import FlaskForm

    # Get checkout details from session or database
    amount = session.get("checkout_amount", 100.00)
    description = session.get("checkout_description", "Payment")

    # Create empty form for CSRF token
    form = FlaskForm()

    return render_template(
        "payment/checkout.html",
        checkout_id=checkout_id,
        amount=amount,
        description=description,
        form=form,
    )


@bp.route("/checkout/<checkout_id>/process", methods=["POST"])
def process_checkout(checkout_id):
    """Process payment for a checkout"""
    try:
        # Get and validate form data
        card_number = request.form.get("card_number", "").replace(" ", "")
        card_name = request.form.get("card_name", "")
        expiry_month = request.form.get("expiry_month", "")
        expiry_year = request.form.get("expiry_year", "")
        cvv = request.form.get("cvv", "")

        if not PaymentProcessingService.validate_card_details(
            card_number, card_name, expiry_month, expiry_year, cvv
        ):
            flash("Please fill in all card details", "error")
            return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))

        # Process payment with SumUp
        sumup_service = SumUpService()
        result = sumup_service.process_checkout_payment(
            checkout_id=checkout_id,
            card_number=card_number,
            card_name=card_name,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
        )

        if not result.get("success"):
            return PaymentProcessingService.handle_payment_failure(checkout_id, result)

        # Payment successful - determine payment type and handle accordingly
        user_id = get_user_id_from_session(current_user)

        # Handle signup payment
        if session.get("signup_user_id"):
            return PaymentProcessingService.handle_signup_payment(
                user_id, checkout_id, result
            )

        # Handle membership renewal
        if session.get("membership_renewal_user_id"):
            return PaymentProcessingService.handle_membership_renewal(
                user_id, checkout_id, result
            )

        # Handle credit purchase
        if session.get("credit_purchase_user_id"):
            return PaymentProcessingService.handle_credit_purchase(
                user_id, checkout_id, result
            )

        # Default success response
        flash("Payment processed successfully!", "success")
        return redirect(
            url_for("member.dashboard")
            if current_user.is_authenticated
            else url_for("auth.login")
        )

    except Exception as e:
        current_app.logger.error(f"Error processing checkout: {str(e)}")
        flash("An error occurred processing your payment. Please try again.", "error")
        return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))

        return redirect(url_for("payment.show_checkout", checkout_id=checkout_id))


@bp.route("/membership", methods=["GET", "POST"])
@login_required
def membership_payment():
    """Membership payment page"""
    if request.method == "POST":
        user = current_user
        amount = current_app.config["ANNUAL_MEMBERSHIP_COST"]

        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency="EUR",
            payment_type="membership",
            payment_method="online",
            description=f"Annual Membership - {user.name}",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Create SumUp checkout
        sumup_service = SumUpService()
        checkout_reference = f"membership_{user.id}_{payment.id}"

        checkout = sumup_service.create_checkout(
            amount=amount,
            currency="EUR",
            description=f"Annual Membership - {user.name}",
            checkout_reference=checkout_reference,
        )

        if checkout:
            # Store info in session for payment processing
            session["membership_renewal_user_id"] = user.id
            session["membership_renewal_payment_id"] = payment.id
            session["checkout_amount"] = float(amount)
            session["checkout_description"] = f"Annual Membership - {user.name}"

            # Redirect to custom payment form
            return redirect(
                url_for("payment.show_checkout", checkout_id=checkout.get("id"))
            )
        else:
            flash("Error creating payment. Please try again.", "error")
            db.session.delete(payment)
            db.session.commit()

    return render_template("payment/membership.html")


@bp.route("/credits", methods=["GET", "POST"])
@login_required
def credits():
    """Purchase additional shooting credits"""
    if request.method == "POST":
        user = current_user
        quantity = int(request.form.get("quantity", 1))
        amount = quantity * current_app.config["ADDITIONAL_NIGHT_COST"]

        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency="EUR",
            payment_type="credits",
            payment_method="online",
            description=f"{quantity} shooting credits",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Create SumUp checkout
        sumup_service = SumUpService()
        checkout_reference = f"credits_{user.id}_{payment.id}"

        checkout = sumup_service.create_checkout(
            amount=amount,
            currency="EUR",
            description=f"{quantity} credits - {user.name}",
            checkout_reference=checkout_reference,
        )

        if checkout:
            # Store info in session for payment processing
            session["credit_purchase_user_id"] = user.id
            session["credit_purchase_payment_id"] = payment.id
            session["credit_purchase_quantity"] = quantity
            session["checkout_amount"] = float(amount)
            session["checkout_description"] = f"{quantity} credits - {user.name}"

            # Redirect to custom payment form
            return redirect(
                url_for("payment.show_checkout", checkout_id=checkout.get("id"))
            )
        else:
            flash("Error creating payment. Please try again.", "error")
            db.session.delete(payment)
            db.session.commit()

    return render_template("payment/credits.html")


@bp.route("/history")
@login_required
def history():
    """View payment history"""
    user = current_user
    payments = (
        Payment.query.filter_by(user_id=user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return render_template("payment/history.html", payments=payments)
