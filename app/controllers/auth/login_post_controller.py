from flask import flash, redirect, render_template, request, url_for
from flask_login import login_user

from app.controllers import BaseController
from app.forms import LoginForm
from app.services import UserService


class LoginPostController(BaseController):
    def __init__(self):
        super().__init__()
        self.service = UserService

    def __call__(self):
        form = LoginForm()

        if form.validate_on_submit():
            remember = request.form.get("remember", False)
            user = self.service.authenticate(form.email.data, form.password.data)

            if user is None:
                flash("Invalid username or password.", "error")
            elif not user.is_active:
                flash("Your account is not currently active.", "error")
            else:
                login_user(user, remember=remember)
                flash("Logged in successfully!", "success")
                next_page = request.args.get("next")
                return redirect(next_page) if next_page else redirect(url_for("member.dashboard"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("auth/login.html", form=form)
