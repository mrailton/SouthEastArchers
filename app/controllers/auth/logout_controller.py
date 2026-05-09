from flask import flash, redirect, url_for
from flask_login import login_required


class LogoutController:
    def __init__(self):
        super().__init__()
        from flask_login import logout_user

        self.logout_user = logout_user

    @login_required
    def __call__(self):
        self.logout_user()
        flash("Logged out successfully!", "success")
        return redirect(url_for("public.index"))
