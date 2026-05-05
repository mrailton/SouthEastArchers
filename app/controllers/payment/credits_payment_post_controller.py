from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.controllers import BaseController
from app.controllers.payment import MAX_CREDIT_QUANTITY
from app.services import PaymentService


class CreditsPaymentPostController(BaseController):
    def __init__(self):
        super().__init__()
        self.payment_service = PaymentService

    @login_required
    def __call__(self):
        try:
            quantity = int(request.form.get("quantity", 1))
        except ValueError, TypeError:
            flash("Invalid quantity.", "error")
            return render_template("payment/credits.html")

        if quantity < 1 or quantity > MAX_CREDIT_QUANTITY:
            flash(f"Quantity must be between 1 and {MAX_CREDIT_QUANTITY}.", "error")
            return render_template("payment/credits.html")

        payment_service = self.payment_service()
        result = payment_service.initiate_credit_purchase(current_user, quantity)

        if result.success:
            data = result.data
            assert data is not None
            session["credit_purchase_user_id"] = data["user_id"]
            session["credit_purchase_payment_id"] = data["payment_id"]
            session["credit_purchase_quantity"] = data["quantity"]
            session["checkout_amount"] = data["amount"]
            session["checkout_description"] = data["description"]
            return redirect(url_for("payment.show_checkout", checkout_id=data["checkout_id"]))
        else:
            flash(result.message, "error")

        return render_template("payment/credits.html")
