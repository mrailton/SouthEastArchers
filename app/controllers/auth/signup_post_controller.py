from flask import flash, redirect, render_template, url_for

from app.controllers import BaseController
from app.events import user_registered
from app.forms import SignupForm
from app.services import UserService


class SignupPostController(BaseController):
    """Handle signup form submission"""

    def __init__(self):
        super().__init__()
        self.service = UserService

    def __call__(self):
        form = SignupForm()

        if form.validate_on_submit():
            result = self.service.create_user(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,
                phone=form.phone.data,
                qualification=form.qualification.data,
                qualification_detail=form.qualification_detail.data,
            )

            if not result.success:
                flash(result.message, "error")
                return render_template("auth/signup.html", form=form)

            user = result.data
            assert user is not None
            user_registered.send(user_id=user.id)

            flash("Thank you for signing up. A coach will review your information shortly and get back to you to discuss membership.", "success")
            return redirect(url_for("auth.login"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("auth/signup.html", form=form)
