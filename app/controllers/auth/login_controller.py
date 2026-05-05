from flask import render_template

from app.forms import LoginForm


class LoginController:
    def __call__(self):
        return render_template("auth/login.html", form=LoginForm())
