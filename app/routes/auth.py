from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, login_user, logout_user

from app.forms import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignupForm
from app.models import User
from app.services import UserService
from app.utils.email import send_password_reset_email

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        remember = request.form.get("remember", False)
        user = UserService.authenticate(form.email.data, form.password.data)

        if user is None:
            flash("Invalid username or password.", "error")
        elif not user.is_active:
            flash("Your account is not currently active.", "error")
        else:
            login_user(user, remember=remember)
            flash("Logged in successfully!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("member.dashboard"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("auth/login.html", form=form)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        user, error = UserService.create_user(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            phone=form.phone.data,
            qualification=form.qualification.data,
        )

        if error:
            flash(error, "error")
            return render_template("auth/signup.html", form=form)

        flash("Thank you for signing up. A coach will review your information shortly and get back to you to discuss membership.", "success")
        return redirect(url_for("auth.login"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("auth/signup.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("public.index"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            token = UserService.create_password_reset_token(user)

            try:
                send_password_reset_email(user, token)
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
                flash("An error occurred sending the email. Please try again later.", "error")
                return render_template("auth/forgot_password.html", form=form)

        flash("If an account exists with that email, you will receive a password reset link.", "info")
        return redirect(url_for("auth.login"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("auth/forgot_password.html", form=form)


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_reset_token(token, max_age=86400)
    if not user:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        success, message = UserService.reset_password(token, form.password.data)

        if success:
            flash(f"{message} Please login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(message, "error")
            return redirect(url_for("auth.forgot_password"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("auth/reset_password.html", token=token, form=form)
