from flask import flash, redirect, render_template, url_for
from flask_login import current_user


class MembershipController:
    def __call__(self):
        if current_user.is_authenticated and current_user.has_active_membership:
            flash("You already have an active membership", "error")
            return redirect(url_for("member.dashboard"))

        return render_template("public/membership.html")
