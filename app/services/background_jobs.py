"""Background job tasks for async processing using RQ"""

from flask import current_app, render_template, url_for
from flask_mail import Message

from app import db, mail
from app.models import Membership, Payment, User


def send_payment_receipt_job(user_id, payment_id):
    """
    Background job: Send payment receipt email to user

    Args:
        user_id: User ID
        payment_id: Payment ID
    """
    # Import here to avoid circular dependency
    from app.utils.email import send_payment_receipt

    user = db.session.get(User, user_id)
    payment = db.session.get(Payment, payment_id)

    if not user or not payment:
        current_app.logger.error(
            f"User {user_id} or Payment {payment_id} not found for receipt email"
        )
        return

    membership = user.membership

    # Send receipt email
    send_payment_receipt(user, payment, membership)
    current_app.logger.info(
        f"Payment receipt sent to {user.email} for payment {payment_id}"
    )


def send_password_reset_job(user_id, token):
    """
    Background job: Send password reset email

    Args:
        user_id: User ID
        token: Reset token
    """
    user = db.session.get(User, user_id)

    if not user:
        current_app.logger.error(f"User {user_id} not found for password reset")
        return

    reset_url = url_for("auth.reset_password", token=token, _external=True)

    html_body = render_template(
        "email/password_reset.html", name=user.name, reset_url=reset_url
    )
    text_body = render_template(
        "email/password_reset.txt", name=user.name, reset_url=reset_url
    )

    msg = Message(
        subject="Reset Your Password - South East Archers",
        recipients=[user.email],
        body=text_body,
        html=html_body,
    )
    mail.send(msg)

    current_app.logger.info(f"Password reset email sent to {user.email}")


def send_membership_expiry_reminder_job(user_id):
    """
    Background job: Send membership expiry reminder

    Args:
        user_id: User ID
    """
    user = db.session.get(User, user_id)

    if not user or not user.membership:
        current_app.logger.error(
            f"User {user_id} or membership not found for expiry reminder"
        )
        return

    membership = user.membership
    days_until_expiry = (membership.expiry_date - membership.expiry_date.today()).days

    renewal_url = url_for("payment.membership_payment", _external=True)

    html_body = render_template(
        "email/membership_expiry_reminder.html",
        name=user.name,
        expiry_date=membership.expiry_date.strftime("%d %B %Y"),
        days_until_expiry=days_until_expiry,
        renewal_url=renewal_url,
    )
    text_body = render_template(
        "email/membership_expiry_reminder.txt",
        name=user.name,
        expiry_date=membership.expiry_date.strftime("%d %B %Y"),
        days_until_expiry=days_until_expiry,
        renewal_url=renewal_url,
    )

    msg = Message(
        subject="Membership Expiry Reminder - South East Archers",
        recipients=[user.email],
        body=text_body,
        html=html_body,
    )
    mail.send(msg)

    current_app.logger.info(
        f"Membership expiry reminder sent to {user.email} ({days_until_expiry} days remaining)"
    )


def check_expiring_memberships_job():
    """
    Background job: Check for memberships expiring in next 7 days and send reminders

    This should be run daily via cron or scheduled task
    """
    from datetime import date, timedelta

    # Get memberships expiring in 7 days
    expiry_date = date.today() + timedelta(days=7)

    expiring_memberships = (
        Membership.query.filter(
            Membership.expiry_date == expiry_date, Membership.status == "active"
        )
        .join(User)
        .filter(User.is_active == True)  # noqa: E712
        .all()
    )

    count = 0
    for membership in expiring_memberships:
        try:
            send_membership_expiry_reminder_job(membership.user_id)
            count += 1
        except Exception as e:
            current_app.logger.error(
                f"Failed to send expiry reminder to user {membership.user_id}: {str(e)}"
            )

    current_app.logger.info(
        f"Sent {count} membership expiry reminders for {len(expiring_memberships)} expiring memberships"
    )
