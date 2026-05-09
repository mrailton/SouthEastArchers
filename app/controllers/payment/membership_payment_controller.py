from flask import render_template
from flask_login import login_required


class MembershipPaymentController:
    @login_required
    def __call__(self):
        return render_template("payment/membership.html")
