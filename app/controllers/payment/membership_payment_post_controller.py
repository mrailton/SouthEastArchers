from flask import flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required

from app.services import PaymentService


class MembershipPaymentPostController:
    @login_required
    def __call__(self):
        payment_service = PaymentService()
        result = payment_service.initiate_membership_payment(current_user)

        if result.success:
            data = result.data
            assert data is not None
            session["membership_renewal_user_id"] = data["user_id"]
            session["membership_renewal_payment_id"] = data["payment_id"]
            session["checkout_amount"] = data["amount"]
            session["checkout_description"] = data["description"]
            return redirect(url_for("payment.show_checkout", checkout_id=data["checkout_id"]))
        else:
            flash(result.message, "error")

        return render_template("payment/membership.html")
