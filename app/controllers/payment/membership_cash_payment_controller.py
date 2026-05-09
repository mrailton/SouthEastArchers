from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.enums import PaymentType
from app.services import PaymentService


class MembershipCashPaymentController:
    @login_required
    def __call__(self):
        payment_service = PaymentService()
        result = payment_service.initiate_cash_membership_payment(current_user)

        if result.success:
            data = result.data
            assert data is not None
            return render_template(
                "payment/cash_pending.html",
                payment_type=PaymentType.MEMBERSHIP,
                amount=data["amount"],
                instructions=data["instructions"],
            )
        else:
            flash(result.message, "error")
            return redirect(url_for("payment.membership_payment"))
