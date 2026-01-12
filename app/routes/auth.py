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

from app.models import User
from app.schemas import ForgotPasswordSchema, LoginSchema, ResetPasswordSchema, SignupSchema
from app.services import UserService
from app.utils.email import send_password_reset_email
from app.utils.pydantic_helpers import validate_request

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.post("/login")
def store_login():
    validated, errors = validate_request(LoginSchema, request)

    if errors or validated is None:
        for field, error in (errors or {}).items():
            flash(error, "error")
        return render_template("auth/login.html")

    remember = request.form.get("remember", False)
    user = UserService.authenticate(validated.email, validated.password)

    if user is None:
        flash("Invalid username or password.", "error")

        return render_template("auth/login.html")
    elif not user.is_active:
        flash("Your account is not currently active.", "error")

        return render_template("auth/login.html")
    else:
        login_user(user, remember=remember)
        flash("Logged in successfully!", "success")
        next_page = request.args.get("next")

        return redirect(next_page) if next_page else redirect(url_for("member.dashboard"))


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        validated, errors = validate_request(SignupSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("auth/signup.html")

        user, error = UserService.create_user(
            name=validated.name,
            email=validated.email,
            password=validated.password,
            phone=validated.phone,
            qualification=validated.qualification,
        )

        if error:
            flash(error, "error")
            return render_template("auth/signup.html")

        flash("Thank you for signing up. A coach will review your information shortly and get back to you to discuss membership.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("public.index"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        validated, errors = validate_request(ForgotPasswordSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("auth/forgot_password.html")

        user = User.query.filter_by(email=validated.email).first()

        if user:
            token = UserService.create_password_reset_token(user)

            try:
                send_password_reset_email(user, token)
            except Exception as e:
                current_app.logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
                flash("An error occurred sending the email. Please try again later.", "error")
                return render_template("auth/forgot_password.html")

        flash("If an account exists with that email, you will receive a password reset link.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_reset_token(token, max_age=86400)
    if not user:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        validated, errors = validate_request(ResetPasswordSchema, request)

        if errors or validated is None:
            for field, error in (errors or {}).items():
                flash(error, "error")
            return render_template("auth/reset_password.html", token=token)

        success, message = UserService.reset_password(token, validated.password)

        if success:
            flash(f"{message} Please login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(message, "error")
            return redirect(url_for("auth.forgot_password"))

    return render_template("auth/reset_password.html", token=token)
