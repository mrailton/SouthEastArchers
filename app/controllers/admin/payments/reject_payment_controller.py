from flask import abort, current_app, flash, redirect, request, url_for

from app.enums import PaymentMethod
from app.repositories import PaymentRepository, UserRepository
from app.utils import permission_required


class RejectPaymentController:
    def __init__(self):
        super().__init__()
        self.payment_repository = PaymentRepository
        self.user_repository = UserRepository

    @permission_required("payments.approve")
    def __call__(self, payment_id):
        redirect_to = request.form.get("redirect_to") or url_for("admin.pending_payments")

        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            abort(404)

        if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
            flash("This payment cannot be rejected.", "error")
            return redirect(redirect_to)

        user = self.user_repository.get_by_id(payment.user_id)
        user_name = user.name if user else "Unknown"

        try:
            payment.status = "cancelled"
            self.payment_repository.save()
            flash(f"Payment rejected for {user_name}.", "success")
        except Exception as e:
            current_app.logger.error(f"Error rejecting payment: {str(e)}")
            flash(f"Error rejecting payment: {str(e)}", "error")

        return redirect(redirect_to)
