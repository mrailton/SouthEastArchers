from flask import render_template
from flask_login import login_required

from app.controllers import BaseController
from app.forms import ChangePasswordForm


class ChangePasswordController(BaseController):
    @login_required
    def __call__(self):
        return render_template("member/change_password.html", form=ChangePasswordForm())
