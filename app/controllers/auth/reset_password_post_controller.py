from flask import flash, redirect, render_template, url_for

from app.controllers import BaseController
from app.forms import ResetPasswordForm
from app.models import User
from app.services import UserService


class ResetPasswordPostController(BaseController):
    """Handle reset password form submission"""

    def __init__(self):
        super().__init__()
        self.service = UserService

    def __call__(self, token):
        user = User.verify_reset_token(token, max_age=86400)
        if not user:
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for("auth.forgot_password"))

        form = ResetPasswordForm()

        if form.validate_on_submit():
            result = self.service.reset_password(token, form.password.data)

            if result.success:
                flash(f"{result.message} Please login.", "success")
                return redirect(url_for("auth.login"))
            else:
                flash(result.message, "error")
                return redirect(url_for("auth.forgot_password"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("auth/reset_password.html", token=token, form=form)
