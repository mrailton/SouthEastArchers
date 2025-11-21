"""Email utility functions"""

from datetime import datetime

from flask import current_app, render_template, url_for
from flask_mail import Message

from app import mail


def send_payment_receipt(user, payment, membership):
    """
    Send payment receipt email to user

    Args:
        user: User object
        payment: Payment object
        membership: Membership object
    """
    try:
        # Generate receipt number
        receipt_number = f"SEA-{payment.id:06d}"

        # Format payment method display
        payment_method_display = {
            "online": "Credit/Debit Card (SumUp)",
            "cash": "Cash Payment",
        }.get(payment.payment_method, payment.payment_method.title())

        # Prepare template data
        template_data = {
            "name": user.name,
            "receipt_number": receipt_number,
            "payment_date": payment.created_at.strftime("%d %B %Y at %H:%M"),
            "description": payment.description or "Annual Membership",
            "payment_method": payment_method_display,
            "transaction_id": (
                payment.sumup_transaction_id
                if payment.payment_method == "online"
                else None
            ),
            "amount": payment.amount,
            "membership_start": membership.start_date.strftime("%d %B %Y"),
            "membership_expiry": membership.expiry_date.strftime("%d %B %Y"),
            "credits": membership.credits,
            "login_url": url_for("auth.login", _external=True),
        }

        # Render email templates
        html_body = render_template("email/payment_receipt.html", **template_data)
        text_body = render_template("email/payment_receipt.txt", **template_data)

        # Create message
        msg = Message(
            subject="Payment Receipt - South East Archers",
            recipients=[user.email],
            html=html_body,
            body=text_body,
        )

        # Send email
        mail.send(msg)
        current_app.logger.info(f"Payment receipt sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error sending payment receipt: {str(e)}")
        return False


def send_welcome_email(user, membership):
    """
    Send welcome email to new member (without payment details)

    Args:
        user: User object
        membership: Membership object
    """
    try:
        # You can create welcome email templates later
        # For now, we'll just use a simple message
        html_body = f"""
        <html>
        <body>
            <h1>Welcome to South East Archers!</h1>
            <p>Dear {user.name},</p>
            <p>Welcome to South East Archers! Your membership is now active.</p>
            <p><strong>Membership Details:</strong></p>
            <ul>
                <li>Start Date: {membership.start_date.strftime('%d %B %Y')}</li>
                <li>Expiry Date: {membership.expiry_date.strftime('%d %B %Y')}</li>
                <li>Credits: {membership.credits} shooting nights</li>
            </ul>
            <p><a href="{url_for('auth.login', _external=True)}">Login to your account</a></p>
            <p>Best regards,<br>South East Archers</p>
        </body>
        </html>
        """

        msg = Message(
            subject="Welcome to South East Archers!",
            recipients=[user.email],
            html=html_body,
        )

        mail.send(msg)
        current_app.logger.info(f"Welcome email sent to {user.email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error sending welcome email: {str(e)}")
        return False
