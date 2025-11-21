from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
from app import db, mail
from app.models import User, Membership, Payment
from app.services import SumUpService
from datetime import date, timedelta
import secrets

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember", False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            flash("Logged in successfully!", "success")
            next_page = request.args.get("next")
            return (
                redirect(next_page)
                if next_page
                else redirect(url_for("member.dashboard"))
            )
        else:
            flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    """User registration"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        dob_str = request.form.get("date_of_birth")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        payment_method = request.form.get("payment_method", "online")

        # Validation
        if not all([name, email, dob_str, password, payment_method]):
            flash("All required fields must be filled.", "error")
            return render_template(
                "auth/signup.html",
                name=name,
                email=email,
                phone=phone,
                date_of_birth=dob_str,
                payment_method=payment_method,
            )

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template(
                "auth/signup.html",
                name=name,
                email=email,
                phone=phone,
                date_of_birth=dob_str,
                payment_method=payment_method,
            )

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template(
                "auth/signup.html",
                name=name,
                email=email,
                phone=phone,
                date_of_birth=dob_str,
                payment_method=payment_method,
            )

        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            flash("Invalid date of birth.", "error")
            return render_template(
                "auth/signup.html",
                name=name,
                email=email,
                phone=phone,
                date_of_birth=dob_str,
                payment_method=payment_method,
            )

        # Create user
        user = User(name=name, email=email, phone=phone, date_of_birth=dob)
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        # Create membership (pending by default)
        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="pending",
        )
        db.session.add(membership)

        # Create payment record
        amount = current_app.config["ANNUAL_MEMBERSHIP_COST"]
        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency="EUR",
            payment_type="membership",
            payment_method=payment_method,
            description=f"Annual Membership for {name}",
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()

        # Handle payment method
        if payment_method == "online":
            # Create SumUp checkout
            sumup_service = SumUpService()

            # Generate unique checkout reference
            checkout_reference = f"membership_{user.id}_{payment.id}"

            # Include user name in description for easy matching in SumUp
            checkout = sumup_service.create_checkout(
                amount=amount,
                currency="EUR",
                description=f"Annual Membership - {name}",
                checkout_reference=checkout_reference,
            )

            if checkout:
                # Store info in session for payment processing
                session["signup_user_id"] = user.id
                session["signup_payment_id"] = payment.id
                session["checkout_amount"] = float(amount)
                session["checkout_description"] = f"Annual Membership - {name}"

                # Redirect to our custom payment form
                return redirect(
                    url_for("payment.show_checkout", checkout_id=checkout.get("id"))
                )
            else:
                flash(
                    "Error creating payment. Please contact us to complete registration.",
                    "error",
                )
                return redirect(url_for("auth.login"))
        else:
            # Cash payment - membership remains pending until admin activates
            flash(
                "Account created! Your membership will be activated once payment is received.",
                "info",
            )
            return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@bp.route("/logout")
@login_required
def logout():
    """User logout"""
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("public.index"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Forgot password request"""
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.generate_reset_token()
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            current_app.logger.info(
                f"Attempting to send password reset email to {user.email}"
            )
            current_app.logger.debug(
                f'Mail server: {current_app.config.get("MAIL_SERVER")}:{current_app.config.get("MAIL_PORT")}'
            )
            current_app.logger.debug(
                f'Mail TLS: {current_app.config.get("MAIL_USE_TLS")}'
            )
            current_app.logger.debug(
                f'Mail username: {current_app.config.get("MAIL_USERNAME")}'
            )
            current_app.logger.debug(
                f'Mail sender: {current_app.config.get("MAIL_DEFAULT_SENDER")}'
            )

            msg = Message(
                "Password Reset Request",
                recipients=[user.email],
                html=render_template(
                    "email/reset_password.html", user=user, reset_url=reset_url
                ),
            )

            try:
                mail.send(msg)
                current_app.logger.info(f"Password reset email sent to {user.email}")
            except Exception as e:
                current_app.logger.error(
                    f"Failed to send password reset email to {user.email}: {str(e)}",
                    exc_info=True,
                )
                flash(
                    "An error occurred sending the email. Please try again later.",
                    "error",
                )
                return render_template("auth/forgot_password.html")

        flash(
            "If an account exists with that email, you will receive a password reset link.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset password with token"""
    user = User.verify_reset_token(token)

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

        user.set_password(password)
        db.session.commit()

        flash("Password reset successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
