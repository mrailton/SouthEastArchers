from flask import current_app, has_app_context, render_template, url_for
from flask_mail import Message

from app import db, mail
from app.models import Payment, User


def _get_app_context():
    if has_app_context():
        return None
    else:
        from app import create_app

        app = create_app()
        return app.app_context()


def send_payment_receipt_job(user_id, payment_id):
    ctx = _get_app_context()
    try:
        if ctx:
            ctx.push()

        from app.utils.email import send_payment_receipt

        user = db.session.get(User, user_id)
        payment = db.session.get(Payment, payment_id)

        if not user or not payment:
            current_app.logger.error(f"User {user_id} or Payment {payment_id} not found for receipt email")
            return

        membership = user.membership

        send_payment_receipt(user, payment, membership)
    finally:
        if ctx:
            ctx.pop()


def send_password_reset_job(user_id, token):
    ctx = _get_app_context()
    try:
        if ctx:
            ctx.push()

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
    finally:
        if ctx:
            ctx.pop()
