from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers import BaseController


class CreditsPaymentController(BaseController):
    @login_required
    def __call__(self):
        if not current_user.membership:
            flash("You must have an active membership to purchase credits.", "error")
            return redirect(url_for("payment.membership_payment"))

        return render_template("payment/credits.html")
