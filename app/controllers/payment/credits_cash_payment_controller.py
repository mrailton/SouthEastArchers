from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.controllers import BaseController
from app.controllers.payment import MAX_CREDIT_QUANTITY
from app.enums import PaymentType
from app.services import PaymentService


class CreditsCashPaymentController(BaseController):
    def __init__(self):
        super().__init__()
        self.payment_service = PaymentService

    @login_required
    def __call__(self):
        try:
            quantity = int(request.form.get("quantity", 1))
        except ValueError, TypeError:
            flash("Invalid quantity.", "error")
            return redirect(url_for("payment.credits"))

        if quantity < 1 or quantity > MAX_CREDIT_QUANTITY:
            flash(f"Quantity must be between 1 and {MAX_CREDIT_QUANTITY}.", "error")
            return redirect(url_for("payment.credits"))

        payment_service = self.payment_service()
        result = payment_service.initiate_cash_credit_purchase(current_user, quantity)

        if result.success:
            data = result.data
            assert data is not None
            return render_template(
                "payment/cash_pending.html",
                payment_type=PaymentType.CREDITS,
                amount=data["amount"],
                quantity=data["quantity"],
                instructions=data["instructions"],
            )
        else:
            flash(result.message, "error")
            return redirect(url_for("payment.credits"))
