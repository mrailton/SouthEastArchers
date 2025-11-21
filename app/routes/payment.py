from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from flask_login import login_required, current_user
from app import db
from app.models import User, Payment, Credit, Membership
from app.services import SumUpService
from app.utils.email import send_payment_receipt
from datetime import date, timedelta

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
        # Get form data
        card_number = request.form.get("card_number", "").replace(" ", "")
        card_name = request.form.get("card_name", "")
        expiry_month = request.form.get("expiry_month", "")
        expiry_year = request.form.get("expiry_year", "")
        cvv = request.form.get("cvv", "")

        # Validate
        if not all([card_number, card_name, expiry_month, expiry_year, cvv]):
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

        if result.get("success"):
            # Payment successful (status = PAID)
            # Check what type of payment this was
            user_id = (
                session.get("signup_user_id")
                or session.get("membership_renewal_user_id")
                or session.get("credit_purchase_user_id")
                or (current_user.id if current_user.is_authenticated else None)
            )

            # Handle signup payment
            if session.get("signup_user_id"):
                payment_id = session.get("signup_payment_id")
                payment = db.session.get(Payment, payment_id)
                user = db.session.get(User, user_id)

                if payment and user:
                    transaction_id = result.get("transaction_id") or checkout_id
                    payment.mark_completed(transaction_id)
                    if user.membership:
                        user.membership.activate()
                    db.session.commit()

                    # Send payment receipt email
                    try:
                        send_payment_receipt(user, payment, user.membership)
                    except Exception as e:
                        current_app.logger.error(
                            f"Failed to send receipt email: {str(e)}"
                        )

                    session.pop("signup_user_id", None)
                    session.pop("signup_payment_id", None)
                    session.pop("checkout_amount", None)
                    session.pop("checkout_description", None)

                    flash(
                        "Payment successful! Your membership is now active. A receipt has been sent to your email.",
                        "success",
                    )
                    return redirect(url_for("auth.login"))

            # Handle membership renewal
            elif session.get("membership_renewal_user_id"):
                payment_id = session.get("membership_renewal_payment_id")
                payment = db.session.get(Payment, payment_id)
                user = db.session.get(User, user_id)

                if payment and user:
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
                        current_app.logger.error(
                            f"Failed to send receipt email: {str(e)}"
                        )

                    session.pop("membership_renewal_user_id", None)
                    session.pop("membership_renewal_payment_id", None)
                    session.pop("checkout_amount", None)
                    session.pop("checkout_description", None)

                    flash(
                        "Membership renewed successfully! A receipt has been sent to your email.",
                        "success",
                    )
                    return redirect(url_for("member.dashboard"))

            # Handle credit purchase
            elif session.get("credit_purchase_user_id"):
                payment_id = session.get("credit_purchase_payment_id")
                quantity = session.get("credit_purchase_quantity", 1)
                payment = db.session.get(Payment, payment_id)
                user = db.session.get(User, user_id)

                if payment and user:
                    transaction_id = result.get("transaction_id") or checkout_id
                    payment.mark_completed(transaction_id)

                    # Add credits
                    credit = Credit(
                        user_id=user.id, amount=quantity, payment_id=payment.id
                    )
                    db.session.add(credit)
                    db.session.commit()

                    session.pop("credit_purchase_user_id", None)
                    session.pop("credit_purchase_payment_id", None)
                    session.pop("credit_purchase_quantity", None)
                    session.pop("checkout_amount", None)
                    session.pop("checkout_description", None)

                    flash(f"Successfully purchased {quantity} credits!", "success")
                    return redirect(url_for("member.dashboard"))

            flash("Payment processed successfully!", "success")
            return redirect(
                url_for("member.dashboard")
                if current_user.is_authenticated
                else url_for("auth.login")
            )
        else:
            # Payment failed or pending
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

    except Exception as e:
        current_app.logger.error(f"Error processing checkout: {str(e)}")
        flash("An error occurred processing your payment. Please try again.", "error")
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
