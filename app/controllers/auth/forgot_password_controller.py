from flask import render_template

from app.forms import ForgotPasswordForm


class ForgotPasswordController:
    """Display forgot password form"""

    def __call__(self):
        return render_template("auth/forgot_password.html", form=ForgotPasswordForm())
