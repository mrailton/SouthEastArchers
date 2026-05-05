from flask import current_app, flash, redirect, render_template, url_for

from app.controllers import BaseController
from app.events import password_reset_requested
from app.forms import ForgotPasswordForm
from app.models import User
from app.services import UserService


class ForgotPasswordPostController(BaseController):
    """Handle forgot password form submission"""

    def __init__(self):
        super().__init__()
        self.service = UserService

    def __call__(self):
        form = ForgotPasswordForm()

        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()

            if user:
                token = self.service.create_password_reset_token(user)

                try:
                    password_reset_requested.send(user_id=user.id, token=token)
                except Exception as e:
                    current_app.logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
                    flash("An error occurred sending the email. Please try again later.", "error")
                    return render_template("auth/forgot_password.html", form=form)

            flash("If an account exists with that email, you will receive a password reset link.", "info")
            return redirect(url_for("auth.login"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("auth/forgot_password.html", form=form)
