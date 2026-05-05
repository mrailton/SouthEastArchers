from flask import render_template

from app.controllers import BaseController
from app.forms import ForgotPasswordForm


class ForgotPasswordController(BaseController):
    """Display forgot password form"""

    def __call__(self):
        return render_template("auth/forgot_password.html", form=ForgotPasswordForm())
