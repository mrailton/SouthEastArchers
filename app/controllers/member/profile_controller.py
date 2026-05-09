from flask import render_template
from flask_login import current_user, login_required

from app.forms import ProfileForm


class ProfileController:
    @login_required
    def __call__(self):
        return render_template("member/profile.html", user=current_user, form=ProfileForm(obj=current_user))
