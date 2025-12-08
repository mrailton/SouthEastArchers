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
from app.services import UserService
from app.utils.email import send_password_reset_email
from app.utils.validation import SignupValidation

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember", False)

        user = UserService.authenticate(email, password)

        if user:
            login_user(user, remember=remember)
            flash("Logged in successfully!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("member.dashboard"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        validated_data, error = SignupValidation.validate_and_extract(request.form)

        if error:
            flash(error, "error")
            return render_template("auth/signup.html")

        user, error = UserService.create_user(
            name=validated_data["name"],
            email=validated_data["email"],
            password=validated_data["password"],
            date_of_birth=validated_data["dob"],
            phone=validated_data.get("phone"),
            payment_method=validated_data["payment_method"],
        )

        if error:
            flash(error, "error")
            return render_template("auth/signup.html")

        if validated_data["payment_method"] == "cash":
            flash("Account created! Your membership will be activated once payment is received.", "info")
            return redirect(url_for("auth.login"))

        result = UserService.initiate_online_payment(user, validated_data["name"])

        if result.get("success"):
            return redirect(url_for("payment.show_checkout", checkout_id=result["checkout_id"]))
        else:
            flash(result.get("error", "Error creating payment. Please contact us."), "error")
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
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

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
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        if not password or not password_confirm:
            flash("Please fill in all fields.", "error")
            return render_template("auth/reset_password.html", token=token)

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/reset_password.html", token=token)

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("auth/reset_password.html", token=token)

        success, message = UserService.reset_password(token, password)

        if success:
            flash(f"{message} Please login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(message, "error")
            return redirect(url_for("auth.forgot_password"))

    return render_template("auth/reset_password.html", token=token)
