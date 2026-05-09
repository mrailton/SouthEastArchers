from datetime import date

from flask import abort, current_app, flash, redirect, request, url_for

from app.enums import PaymentMethod, PaymentType
from app.events import credit_purchased, payment_completed
from app.models import Credit, Membership
from app.repositories import CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services.settings_service import SettingsService
from app.utils import permission_required


class ApprovePaymentController:
    @permission_required("payments.approve")
    def __call__(self, payment_id):
        redirect_to = request.form.get("redirect_to") or url_for("admin.pending_payments")

        payment = PaymentRepository.get_by_id(payment_id)
        if not payment:
            abort(404)

        if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
            flash("This payment cannot be approved.", "error")
            return redirect(redirect_to)

        user = UserRepository.get_by_id(payment.user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(redirect_to)

        try:
            payment.mark_completed(processor="cash")

            if payment.payment_type == PaymentType.MEMBERSHIP:
                if user.membership:
                    if user.membership.status != "active":
                        user.membership.activate()
                    else:
                        expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                        user.membership.renew(expiry_date=expiry_date)
                else:
                    expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                    membership = Membership(
                        user_id=user.id,
                        start_date=date.today(),
                        expiry_date=expiry_date,
                        initial_credits=SettingsService.get("membership_shoots_included"),
                        purchased_credits=0,
                        status="active",
                    )
                    MembershipRepository.add(membership)

            elif payment.payment_type == PaymentType.CREDITS:
                description = payment.description or ""
                quantity = 1
                if "shooting credits" in description.lower():
                    try:
                        quantity = int(description.split()[0])
                    except ValueError, IndexError:
                        quantity = 1

                if user.membership:
                    user.membership.add_credits(quantity)

                credit = Credit(user_id=user.id, amount=quantity, payment_id=payment.id)
                CreditRepository.add(credit)

            PaymentRepository.save()

            try:
                if payment.payment_type == PaymentType.CREDITS:
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
            current_app.logger.error(f"Error approving payment: {str(e)}")
            flash(f"Error approving payment: {str(e)}", "error")

        return redirect(redirect_to)
