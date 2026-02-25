"""Admin routes for managing pending cash payments."""

from datetime import date

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app.events import credit_purchased, payment_completed
from app.models import Credit, Membership
from app.repositories import CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services.settings_service import SettingsService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/payments")
@permission_required("payments.approve")
def pending_payments():
    """Display list of pending cash payments awaiting approval."""
    payments = PaymentRepository.get_pending_cash()

    # Get user info for each payment
    payment_data = []
    for payment in payments:
        user = UserRepository.get_by_id(payment.user_id)
        payment_data.append({"payment": payment, "user": user})

    return render_template("admin/pending_payments.html", payment_data=payment_data)


@bp.post("/payments/<int:payment_id>/approve")
@permission_required("payments.approve")
def approve_payment(payment_id):
    """Approve a pending cash payment."""
    redirect_to = request.form.get("redirect_to") or url_for("admin.pending_payments")

    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        abort(404)

    if payment.status != "pending" or payment.payment_method != "cash":
        flash("This payment cannot be approved.", "error")
        return redirect(redirect_to)

    user = UserRepository.get_by_id(payment.user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(redirect_to)

    try:
        # Mark payment as completed
        payment.mark_completed(processor="cash")

        if payment.payment_type == "membership":
            # Activate, renew, or create membership
            if user.membership:
                if user.membership.status != "active":
                    user.membership.activate()
                else:
                    user.membership.renew()
            else:
                # Create new membership for user (e.g., new signup with cash payment)
                settings = SettingsService.get()
                expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                membership = Membership(
                    user_id=user.id,
                    start_date=date.today(),
                    expiry_date=expiry_date,
                    initial_credits=settings.membership_shoots_included,
                    purchased_credits=0,
                    status="active",
                )
                MembershipRepository.add(membership)

        elif payment.payment_type == "credits":
            # Add credits to membership
            # Extract quantity from description (e.g., "5 shooting credits (Cash)")
            description = payment.description or ""
            quantity = 1
            if "shooting credits" in description.lower():
                try:
                    quantity = int(description.split()[0])
                except ValueError, IndexError:
                    quantity = 1

            if user.membership:
                user.membership.add_credits(quantity)

            # Create credit record
            credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
            CreditRepository.add(credit)

        PaymentRepository.save()

        # Emit event — handler sends receipt email
        try:
            if payment.payment_type == "credits":
                quantity = 1
                if "shooting credits" in (payment.description or "").lower():
                    try:
                        quantity = int(payment.description.split()[0])
                    except ValueError, IndexError:
                        quantity = 1
                credit_purchased.send(user_id=user.id, payment_id=payment.id, quantity=quantity)
            else:
                payment_completed.send(user_id=user.id, payment_id=payment.id, payment_type=payment.payment_type)
        except Exception as e:
            current_app.logger.error(f"Failed to emit payment event: {str(e)}")

        flash(f"Payment approved for {user.name}!", "success")

    except Exception as e:
        # rollback handled by save()
        current_app.logger.error(f"Error approving payment: {str(e)}")
        flash(f"Error approving payment: {str(e)}", "error")

    return redirect(redirect_to)


@bp.post("/payments/<int:payment_id>/reject")
@permission_required("payments.approve")
def reject_payment(payment_id):
    """Reject a pending cash payment."""
    redirect_to = request.form.get("redirect_to") or url_for("admin.pending_payments")

    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        abort(404)

    if payment.status != "pending" or payment.payment_method != "cash":
        flash("This payment cannot be rejected.", "error")
        return redirect(redirect_to)

    user = UserRepository.get_by_id(payment.user_id)
    user_name = user.name if user else "Unknown"

    try:
        payment.status = "cancelled"
        PaymentRepository.save()
        flash(f"Payment rejected for {user_name}.", "success")
    except Exception as e:
        # rollback handled by save()
        current_app.logger.error(f"Error rejecting payment: {str(e)}")
        flash(f"Error rejecting payment: {str(e)}", "error")

    return redirect(redirect_to)
