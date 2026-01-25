from flask import current_app, render_template, url_for
from flask_mail import Message

from app import mail


def send_password_reset_email(user, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    msg = Message(
        "Password Reset Request",
        recipients=[user.email],
        html=render_template("email/reset_password.html", user=user, reset_url=reset_url),
    )

    mail.send(msg)


def send_payment_receipt(user, payment, membership):
    try:
        receipt_number = f"SEA-{payment.id:06d}"

        payment_method_display = {
            "online": "Credit/Debit Card (SumUp)",
            "cash": "Cash Payment",
        }.get(payment.payment_method, payment.payment_method.title())

        try:
            login_url = url_for("auth.login", _external=True)
        except RuntimeError:
            login_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/login"

        template_data = {
            "name": user.name,
            "receipt_number": receipt_number,
            "payment_date": payment.created_at.strftime("%d %B %Y at %H:%M"),
            "description": payment.description or "Annual Membership",
            "payment_method": payment_method_display,
            "transaction_id": (payment.external_transaction_id if payment.payment_method == "online" else None),
            "amount": payment.amount,
            "membership_start": membership.start_date.strftime("%d %B %Y"),
            "membership_expiry": membership.expiry_date.strftime("%d %B %Y"),
            "credits": membership.credits_remaining(),
            "login_url": login_url,
        }

        html_body = render_template("email/payment_receipt.html", **template_data)
        text_body = render_template("email/payment_receipt.txt", **template_data)

        msg = Message(
            subject="Payment Receipt - South East Archers",
            recipients=[user.email],
            html=html_body,
            body=text_body,
        )

        mail.send(msg)
        current_app.logger.info(f"Payment receipt sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error sending payment receipt: {str(e)}")
        return False


def send_welcome_email(user):
    """Send welcome email to new user with membership purchase information."""
    try:
        try:
            login_url = url_for("auth.login", _external=True)
        except RuntimeError:
            login_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/auth/login"

        membership_cost = current_app.config.get("ANNUAL_MEMBERSHIP_COST", 10000)
        credits_included = current_app.config.get("MEMBERSHIP_NIGHTS_INCLUDED", 20)

        msg = Message(
            subject="Welcome to South East Archers!",
            recipients=[user.email],
            html=render_template(
                "email/welcome.html",
                user=user,
                login_url=login_url,
                membership_cost=membership_cost,
                credits_included=credits_included,
            ),
            body=render_template(
                "email/welcome.txt",
                user=user,
                login_url=login_url,
                membership_cost=membership_cost,
                credits_included=credits_included,
            ),
        )

        mail.send(msg)
        current_app.logger.info(f"Welcome email sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error sending welcome email: {str(e)}")
        return False


def send_credit_purchase_receipt(user, payment, credits_purchased, credits_remaining):
    """Send a receipt email for credit purchase."""
    try:
        receipt_number = f"SEA-{payment.id:06d}"

        payment_method_display = {
            "online": "Credit/Debit Card (SumUp)",
            "cash": "Cash Payment",
        }.get(payment.payment_method, payment.payment_method.title())

        try:
            login_url = url_for("member.credits", _external=True)
        except RuntimeError:
            login_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/member/credits"

        template_data = {
            "name": user.name,
            "receipt_number": receipt_number,
            "payment_date": payment.created_at.strftime("%d %B %Y at %H:%M"),
            "description": payment.description or f"{credits_purchased} shooting credits",
            "payment_method": payment_method_display,
            "transaction_id": (payment.external_transaction_id if payment.payment_method == "online" else None),
            "amount": payment.amount,
            "credits_purchased": credits_purchased,
            "credits_remaining": credits_remaining,
            "login_url": login_url,
        }

        html_body = render_template("email/credit_receipt.html", **template_data)
        text_body = render_template("email/credit_receipt.txt", **template_data)

        msg = Message(
            subject="Credit Purchase Receipt - South East Archers",
            recipients=[user.email],
            html=html_body,
            body=text_body,
        )

        mail.send(msg)
        current_app.logger.info(f"Credit purchase receipt sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error sending credit purchase receipt: {str(e)}")
        return False
