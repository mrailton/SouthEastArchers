"""Admin routes for managing pending cash payments."""

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app import db
from app.models import Credit, Payment, User
from app.utils.decorators import permission_required

from . import bp


@bp.get("/payments")
@permission_required("payments.approve")
def pending_payments():
    """Display list of pending cash payments awaiting approval."""
    payments = (
        Payment.query.filter_by(payment_method="cash", status="pending")
        .order_by(Payment.created_at.desc())
        .all()
    )

    # Get user info for each payment
    payment_data = []
    for payment in payments:
        user = db.session.get(User, payment.user_id)
        payment_data.append({"payment": payment, "user": user})

    return render_template("admin/pending_payments.html", payment_data=payment_data)


@bp.post("/payments/<int:payment_id>/approve")
@permission_required("payments.approve")
def approve_payment(payment_id):
    """Approve a pending cash payment."""
    redirect_to = request.form.get("redirect_to") or url_for("admin.pending_payments")

    payment = db.session.get(Payment, payment_id)
    if not payment:
        abort(404)

    if payment.status != "pending" or payment.payment_method != "cash":
        flash("This payment cannot be approved.", "error")
        return redirect(redirect_to)

    user = db.session.get(User, payment.user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(redirect_to)

    try:
        # Mark payment as completed
        payment.mark_completed(processor="cash")

        if payment.payment_type == "membership":
            # Activate or renew membership
            if user.membership:
                if user.membership.status != "active":
                    user.membership.activate()
                else:
                    user.membership.renew()
            else:
                flash("User has no membership to activate.", "error")
                return redirect(redirect_to)

        elif payment.payment_type == "credits":
            # Add credits to membership
            # Extract quantity from description (e.g., "5 shooting credits (Cash)")
            description = payment.description or ""
            quantity = 1
            if "shooting credits" in description.lower():
                try:
                    quantity = int(description.split()[0])
                except (ValueError, IndexError):
                    quantity = 1

            if user.membership:
                user.membership.add_credits(quantity)

            # Create credit record
            credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
            db.session.add(credit)

        db.session.commit()

        # Send receipt email
        try:
            if payment.payment_type == "credits":
                from app.services.mail_service import send_credit_purchase_receipt

                quantity = 1
                if "shooting credits" in (payment.description or "").lower():
                    try:
                        quantity = int(payment.description.split()[0])
                    except (ValueError, IndexError):
                        quantity = 1
                send_credit_purchase_receipt(user.id, payment.id, quantity)
            else:
                from app.services.mail_service import send_payment_receipt

                send_payment_receipt(user.id, payment.id)
        except Exception as e:
            current_app.logger.error(f"Failed to send receipt email: {str(e)}")

        flash(f"Payment approved for {user.name}!", "success")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving payment: {str(e)}")
        flash(f"Error approving payment: {str(e)}", "error")

    return redirect(redirect_to)


@bp.post("/payments/<int:payment_id>/reject")
@permission_required("payments.approve")
def reject_payment(payment_id):
    """Reject a pending cash payment."""
    redirect_to = request.form.get("redirect_to") or url_for("admin.pending_payments")

    payment = db.session.get(Payment, payment_id)
    if not payment:
        abort(404)

    if payment.status != "pending" or payment.payment_method != "cash":
        flash("This payment cannot be rejected.", "error")
        return redirect(redirect_to)

    user = db.session.get(User, payment.user_id)
    user_name = user.name if user else "Unknown"

    try:
        payment.status = "cancelled"
        db.session.commit()
        flash(f"Payment rejected for {user_name}.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting payment: {str(e)}")
        flash(f"Error rejecting payment: {str(e)}", "error")

    return redirect(redirect_to)
