from flask import render_template, session
from flask_login import login_required


class ShowCheckoutController:
    @login_required
    def __call__(self, checkout_id):
        amount = session.get("checkout_amount", 100.00)
        description = session.get("checkout_description", "Payment")

        return render_template(
            "payment/checkout.html",
            checkout_id=checkout_id,
            amount=amount,
            description=description,
        )
