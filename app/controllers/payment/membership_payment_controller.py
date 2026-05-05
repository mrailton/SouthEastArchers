from flask import render_template
from flask_login import login_required

from app.controllers import BaseController


class MembershipPaymentController(BaseController):
    @login_required
    def __call__(self):
        return render_template("payment/membership.html")
