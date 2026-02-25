from flask import current_app, render_template, url_for
from flask_mail import Message

from app import mail


def send_password_reset(user_id: int, token: str) -> None:
    """Send a password reset email."""
    from app.repositories import UserRepository

    try:
        user = UserRepository.get_by_id(user_id)
        if not user:
            current_app.logger.error(f"Cannot send password reset: user {user_id} not found")
            return

        reset_url = url_for("auth.reset_password", token=token, _external=True)

        msg = Message(
            subject="Reset Your Password - South East Archers",
            recipients=[user.email],
            html=render_template("email/reset_password.html", user=user, reset_url=reset_url),
        )
        mail.send(msg)
        current_app.logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e}")


def send_payment_receipt(user_id: int, payment_id: int) -> None:
    """Send a payment receipt email."""
    from app.repositories import PaymentRepository, UserRepository

    try:
        user = UserRepository.get_by_id(user_id)
        payment = PaymentRepository.get_by_id(payment_id)
        if not user or not payment:
            current_app.logger.error(f"Cannot send receipt: user {user_id} or payment {payment_id} not found")
            return

        membership = user.membership
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

        msg = Message(
            subject="Payment Receipt - South East Archers",
            recipients=[user.email],
            html=render_template("email/payment_receipt.html", **template_data),
            body=render_template("email/payment_receipt.txt", **template_data),
        )
        mail.send(msg)
        current_app.logger.info(f"Payment receipt sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send receipt email: {e}")


def send_credit_purchase_receipt(user_id: int, payment_id: int, credits_purchased: int) -> None:
    """Send a credit purchase receipt email."""
    from app.repositories import PaymentRepository, UserRepository

    try:
        user = UserRepository.get_by_id(user_id)
        payment = PaymentRepository.get_by_id(payment_id)
        if not user or not payment:
            current_app.logger.error(f"Cannot send credit receipt: user {user_id} or payment {payment_id} not found")
            return

        credits_remaining = user.membership.credits_remaining()
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

        msg = Message(
            subject="Credit Purchase Receipt - South East Archers",
            recipients=[user.email],
            html=render_template("email/credit_receipt.html", **template_data),
            body=render_template("email/credit_receipt.txt", **template_data),
        )
        mail.send(msg)
        current_app.logger.info(f"Credit purchase receipt sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send credit receipt email: {e}")


def send_welcome_email(user_id: int) -> None:
    """Send a welcome email to a new user."""
    from app.repositories import UserRepository

    try:
        user = UserRepository.get_by_id(user_id)
        if not user:
            current_app.logger.error(f"Cannot send welcome email: user {user_id} not found")
            return

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
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email: {e}")


def send_new_member_notification(new_user_id: int) -> None:
    """Send a notification email to all admins with members.manage_membership permission."""
    from app.repositories import UserRepository

    try:
        new_user = UserRepository.get_by_id(new_user_id)
        if not new_user:
            current_app.logger.error(f"Cannot send notification: user {new_user_id} not found")
            return

        admin_users = UserRepository.get_all_with_permission("members.manage_membership")
        admin_emails: list[str] = [user.email for user in admin_users]

        try:
            admin_url = url_for("admin.members", _external=True)
        except RuntimeError:
            admin_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/admin/members"

        msg = Message(
            subject=f"New Member Sign-Up: {new_user.name} - South East Archers",
            recipients=list(admin_emails),
            html=render_template(
                "email/new_member_notification.html",
                new_member_name=new_user.name,
                new_member_email=new_user.email,
                new_member_phone=new_user.phone,
                new_member_qualification=new_user.qualification,
                admin_url=admin_url,
            ),
            body=render_template(
                "email/new_member_notification.txt",
                new_member_name=new_user.name,
                new_member_email=new_user.email,
                new_member_phone=new_user.phone,
                new_member_qualification=new_user.qualification,
                admin_url=admin_url,
            ),
        )
        mail.send(msg)
        current_app.logger.info(f"New member notification sent to {len(admin_emails)} admin(s) for new member {new_user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send new member notification: {e}")


def send_cash_payment_pending_email(user_id: int, payment_id: int) -> None:
    """Send a confirmation email when a cash payment request is submitted."""
    from app.repositories import PaymentRepository, UserRepository
    from app.services.settings_service import SettingsService

    try:
        user = UserRepository.get_by_id(user_id)
        payment = PaymentRepository.get_by_id(payment_id)
        if not user or not payment:
            current_app.logger.error(f"Cannot send cash payment email: user {user_id} or payment {payment_id} not found")
            return

        settings = SettingsService.get()

        try:
            history_url = url_for("payment.history", _external=True)
        except RuntimeError:
            history_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/payment/history"

        msg = Message(
            subject="Cash Payment Submitted - South East Archers",
            recipients=[user.email],
            html=render_template(
                "email/cash_payment_pending.html",
                name=user.name,
                reference=f"CASH-{payment.id}",
                submitted_date=payment.created_at.strftime("%d %B %Y"),
                description=payment.description,
                amount=payment.amount,
                instructions=settings.cash_payment_instructions,
                payment_type=payment.payment_type,
                history_url=history_url,
            ),
        )
        mail.send(msg)
        current_app.logger.info(f"Cash payment pending email sent to {user.email} for payment {payment_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send cash payment pending email: {e}")
