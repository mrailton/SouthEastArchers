from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.utils.datetime_utils import utc_now
from app.models import User, Membership, Shoot, Credit, Payment
from datetime import datetime

bp = Blueprint("member", __name__, url_prefix="/member")


@bp.route("/dashboard")
@login_required
def dashboard():
    """Member dashboard"""
    user = current_user
    membership = user.membership

    # Get shoot count
    shoots_attended = len(user.shoots)

    return render_template(
        "member/dashboard.html",
        user=user,
        membership=membership,
        shoots_attended=shoots_attended,
    )


@bp.route("/shoots")
@login_required
def shoots():
    """View shoot history"""
    user = current_user

    # Get user's shoot history
    user_shoots = (
        Shoot.query.join(Shoot.users)
        .filter(User.id == user.id)
        .order_by(Shoot.date.desc())
        .all()
    )

    return render_template("member/shoots.html", shoots=user_shoots, user=user)


@bp.route("/credits")
@login_required
def credits():
    """View and purchase credits"""
    user = current_user
    credits = Credit.query.filter_by(user_id=user.id).all()

    return render_template("member/credits.html", credits=credits, user=user)


@bp.route("/profile")
@login_required
def profile():
    """User profile page"""
    user = current_user
    return render_template("member/profile.html", user=user)


@bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Update user profile"""
    user = current_user

    user.name = request.form.get("name", user.name)
    user.phone = request.form.get("phone", user.phone)

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("member.profile"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password"""
    if request.method == "POST":
        user = current_user
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return render_template("member/change_password.html")

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("member/change_password.html")

        user.set_password(new_password)
        db.session.commit()

        flash("Password changed successfully!", "success")
        return redirect(url_for("member.profile"))

    return render_template("member/change_password.html")
