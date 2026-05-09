from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.forms import ChangePasswordForm
from app.services import UserService


class ChangePasswordPostController:
    def __init__(self):
        super().__init__()
        self.service = UserService

    @login_required
    def __call__(self):
        form = ChangePasswordForm()

        if form.validate_on_submit():
            result = self.service.change_password(
                user=current_user,
                current_password=form.current_password.data,
                new_password=form.new_password.data,
            )

            if result.success:
                flash(result.message, "success")
                return redirect(url_for("member.profile"))
            else:
                flash(result.message, "error")

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("member/change_password.html", form=ChangePasswordForm())
