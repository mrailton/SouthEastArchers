from flask import render_template

from app.forms import SignupForm


class SignupController:
    """Display signup form"""

    def __call__(self):
        return render_template("auth/signup.html", form=SignupForm())
