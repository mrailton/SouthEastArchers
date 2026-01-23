from flask import current_app


def send_payment_receipt(user_id: int, payment_id: int) -> None:
    """Send a payment receipt email synchronously."""
    from app import db
    from app.models import Payment, User
    from app.utils.email import send_payment_receipt as util_send

    try:
        user = db.session.get(User, user_id)
        payment = db.session.get(Payment, payment_id)

        if not user or not payment:
            current_app.logger.error(f"Cannot send receipt — user or payment not found (user_id={user_id}, payment_id={payment_id})")
            return

        util_send(user, payment, user.membership)
        current_app.logger.info(f"Sent payment receipt email for user {user_id}, payment {payment_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send receipt email: {e}")


def send_password_reset(user_id: int, token: str) -> None:
    """Send a password reset email synchronously."""
    from flask import render_template, url_for
    from flask_mail import Message

    from app import db, mail
    from app.models import User

    try:
        user = db.session.get(User, user_id)

        if not user:
            current_app.logger.error(f"User {user_id} not found for password reset")
            return

        reset_url = url_for("auth.reset_password", token=token, _external=True)

        html_body = render_template("email/password_reset.html", name=user.name, reset_url=reset_url)
        text_body = render_template("email/password_reset.txt", name=user.name, reset_url=reset_url)

        msg = Message(
            subject="Reset Your Password - South East Archers",
            recipients=[user.email],
            body=text_body,
            html=html_body,
        )
        mail.send(msg)

        current_app.logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e}")


def send_credit_purchase_receipt(user_id: int, payment_id: int, credits_purchased: int) -> None:
    """Send a credit purchase receipt email synchronously."""
    from app import db
    from app.models import Payment, User
    from app.utils.email import send_credit_purchase_receipt as util_send

    try:
        user = db.session.get(User, user_id)
        payment = db.session.get(Payment, payment_id)

        if not user or not payment:
            current_app.logger.error(f"Cannot send credit receipt — user or payment not found (user_id={user_id}, payment_id={payment_id})")
            return

        if not user.membership:
            current_app.logger.error(f"Cannot send credit receipt — user {user_id} has no membership")
            return

        credits_remaining = user.membership.credits
        util_send(user, payment, credits_purchased, credits_remaining)
        current_app.logger.info(f"Sent credit purchase receipt email for user {user_id}, payment {payment_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send credit receipt email: {e}")
