from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms import ChangePasswordForm, ProfileForm
from app.models import Credit, Shoot, User
from app.services import UserService

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


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        success, message = UserService.update_profile(
            user=current_user,
            name=form.name.data,
            phone=form.phone.data,
        )
        flash(message, "success" if success else "error")
        return redirect(url_for("member.profile"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("member/profile.html", user=current_user, form=form)


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        success, message = UserService.change_password(
            user=current_user,
            current_password=form.current_password.data,
            new_password=form.new_password.data,
        )

        if success:
            flash(message, "success")
            return redirect(url_for("member.profile"))
        else:
            flash(message, "error")

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("member/change_password.html", form=form)
