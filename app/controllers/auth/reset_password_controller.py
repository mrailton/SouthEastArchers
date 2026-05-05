from flask import flash, redirect, render_template, url_for

from app.controllers import BaseController
from app.forms import ResetPasswordForm
from app.models import User


class ResetPasswordController(BaseController):
    """Display reset password form"""

    def __call__(self, token):
        user = User.verify_reset_token(token, max_age=86400)
        if not user:
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for("auth.forgot_password"))

        return render_template("auth/reset_password.html", token=token, form=ResetPasswordForm())
