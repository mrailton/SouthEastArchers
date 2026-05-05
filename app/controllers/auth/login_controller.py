from flask import render_template

from app.controllers import BaseController
from app.forms import LoginForm


class LoginController(BaseController):
    def __call__(self):
        return render_template("auth/login.html", form=LoginForm())
