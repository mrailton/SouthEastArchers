from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import Credit, Shoot, User
from app.schemas import ChangePasswordSchema, ProfileSchema
from app.services import UserService
from app.utils.pydantic_helpers import validate_request

bp = Blueprint("member", __name__, url_prefix="/member")


@bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user
    membership = user.membership

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
    user = current_user

    user_shoots = Shoot.query.join(Shoot.users).filter(User.id == user.id).order_by(Shoot.date.desc()).all()

    return render_template("member/shoots.html", shoots=user_shoots, user=user)


@bp.route("/credits")
@login_required
def credits():
    user = current_user
    credits = Credit.query.filter_by(user_id=user.id).all()

    return render_template("member/credits.html", credits=credits, user=user)


@bp.route("/profile")
@login_required
def profile():
    user = current_user
    return render_template("member/profile.html", user=user)


@bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    validated, errors = validate_request(ProfileSchema, request)

    if errors or validated is None:
        for field, error in (errors or {}).items():
            flash(error, "error")
        return redirect(url_for("member.profile"))

    success, message = UserService.update_profile(
        user=current_user,
        name=validated.name,
        phone=validated.phone,
    )
    flash(message, "success" if success else "error")
    return redirect(url_for("member.profile"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        validated, errors = validate_request(ChangePasswordSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("member/change_password.html")

        success, message = UserService.change_password(
            user=current_user,
            current_password=validated.current_password,
            new_password=validated.new_password,
        )

        if success:
            flash(message, "success")
            return redirect(url_for("member.profile"))
        else:
            flash(message, "error")

    return render_template("member/change_password.html")
