from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.forms import ProfileForm
from app.services import UserService


class ProfilePostController:
    def __init__(self):
        super().__init__()
        self.service = UserService

    @login_required
    def __call__(self):
        form = ProfileForm(obj=current_user)

        if form.validate_on_submit():
            result = self.service.update_profile(
                user=current_user,
                name=form.name.data,
                phone=form.phone.data,
            )
            flash(result.message, "success" if result.success else "error")
            return redirect(url_for("member.profile"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("member/profile.html", user=current_user, form=ProfileForm(obj=current_user))
