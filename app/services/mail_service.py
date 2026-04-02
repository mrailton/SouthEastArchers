from collections.abc import Callable

from flask import current_app, render_template, url_for
from flask_mail import Message

from app import mail

_PAYMENT_METHOD_LABELS = {
    "online": "Credit/Debit Card (SumUp)",
    "cash": "Cash Payment",
}


class MailService:
    @staticmethod
    def _safe_url_for(endpoint: str, fallback_path: str, **kwargs) -> str:
        """Generate an external URL, falling back to *SITE_URL* config outside a request context."""
        try:
            return url_for(endpoint, _external=True, **kwargs)
        except RuntimeError:
            return current_app.config.get("SITE_URL", "https://southeastarchers.ie") + fallback_path

    @staticmethod
    def _send(user_id: int, email_type: str, build_message: Callable) -> None:
        """Look up *user_id*, call *build_message(user)* to obtain a ``Message``, and send it.

        If *build_message* returns ``None`` sending is silently skipped (e.g.
        because a related record was not found).  All exceptions are caught and
        logged so that mail failures never propagate to callers.
        """
        from app.repositories import UserRepository

        try:
            user = UserRepository.get_by_id(user_id)
            if not user:
                current_app.logger.error(f"Cannot send {email_type}: user {user_id} not found")
                return

            msg = build_message(user)
            if msg is None:
                return

            mail.send(msg)
            current_app.logger.info(f"{email_type.capitalize()} sent to {user.email}")
        except Exception as e:
            current_app.logger.error(f"Failed to send {email_type}: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def send_password_reset(user_id: int, token: str) -> None:
        """Send a password reset email."""

        def _build(user):
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            return Message(
                subject="Reset Your Password - South East Archers",
                recipients=[user.email],
                html=render_template("email/reset_password.html", user=user, reset_url=reset_url),
            )

        MailService._send(user_id, "password reset email", _build)

    @staticmethod
    def send_payment_receipt(user_id: int, payment_id: int) -> None:
        """Send a payment receipt email."""
        from app.repositories import PaymentRepository

        def _build(user):
            payment = PaymentRepository.get_by_id(payment_id)
            if not payment:
                current_app.logger.error(f"Cannot send receipt: payment {payment_id} not found")
                return None

            template_data = {
                "name": user.name,
                "receipt_number": f"SEA-{payment.id:06d}",
                "payment_date": payment.created_at.strftime("%d %B %Y at %H:%M"),
                "description": payment.description or "Annual Membership",
                "payment_method": _PAYMENT_METHOD_LABELS.get(payment.payment_method, payment.payment_method.title()),
                "transaction_id": payment.external_transaction_id if payment.payment_method == "online" else None,
                "amount": payment.amount,
                "membership_start": user.membership.start_date.strftime("%d %B %Y"),
                "membership_expiry": user.membership.expiry_date.strftime("%d %B %Y"),
                "credits": user.membership.credits_remaining(),
                "login_url": MailService._safe_url_for("auth.login", "/login"),
            }

            return Message(
                subject="Payment Receipt - South East Archers",
                recipients=[user.email],
                html=render_template("email/payment_receipt.html", **template_data),
                body=render_template("email/payment_receipt.txt", **template_data),
            )

        MailService._send(user_id, "receipt email", _build)

    @staticmethod
    def send_credit_purchase_receipt(user_id: int, payment_id: int, credits_purchased: int) -> None:
        """Send a credit purchase receipt email."""
        from app.repositories import PaymentRepository

        def _build(user):
            payment = PaymentRepository.get_by_id(payment_id)
            if not payment:
                current_app.logger.error(f"Cannot send credit receipt: payment {payment_id} not found")
                return None

            template_data = {
                "name": user.name,
                "receipt_number": f"SEA-{payment.id:06d}",
                "payment_date": payment.created_at.strftime("%d %B %Y at %H:%M"),
                "description": payment.description or f"{credits_purchased} shooting credits",
                "payment_method": _PAYMENT_METHOD_LABELS.get(payment.payment_method, payment.payment_method.title()),
                "transaction_id": payment.external_transaction_id if payment.payment_method == "online" else None,
                "amount": payment.amount,
                "credits_purchased": credits_purchased,
                "credits_remaining": user.membership.credits_remaining(),
                "login_url": MailService._safe_url_for("member.credits", "/member/credits"),
            }

            return Message(
                subject="Credit Purchase Receipt - South East Archers",
                recipients=[user.email],
                html=render_template("email/credit_receipt.html", **template_data),
                body=render_template("email/credit_receipt.txt", **template_data),
            )

        MailService._send(user_id, "credit receipt email", _build)

    @staticmethod
    def send_welcome_email(user_id: int) -> None:
        """Send a welcome email to a new user."""
        from app.services.settings_service import SettingsService

        def _build(user):
            login_url = MailService._safe_url_for("auth.login", "/auth/login")
            membership_cost = SettingsService.get("annual_membership_cost")
            credits_included = SettingsService.get("membership_shoots_included")

            return Message(
                subject="Welcome to South East Archers!",
                recipients=[user.email],
                html=render_template("email/welcome.html", user=user, login_url=login_url, membership_cost=membership_cost, credits_included=credits_included),
                body=render_template("email/welcome.txt", user=user, login_url=login_url, membership_cost=membership_cost, credits_included=credits_included),
            )

        MailService._send(user_id, "welcome email", _build)

    @staticmethod
    def send_new_member_notification(new_user_id: int) -> None:
        """Send a notification email to all admins with members.manage_membership permission."""
        from app.repositories import UserRepository

        def _build(new_user):
            admin_users = UserRepository.get_all_with_permission("members.manage_membership")
            admin_url = MailService._safe_url_for("admin.members", "/admin/members")

            return Message(
                subject=f"New Member Sign-Up: {new_user.name} - South East Archers",
                recipients=[u.email for u in admin_users],
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

        MailService._send(new_user_id, "new member notification", _build)

    @staticmethod
    def send_cash_payment_pending_email(user_id: int, payment_id: int) -> None:
        """Send a confirmation email when a cash payment request is submitted."""
        from app.repositories import PaymentRepository
        from app.services.settings_service import SettingsService

        def _build(user):
            payment = PaymentRepository.get_by_id(payment_id)
            if not payment:
                current_app.logger.error(f"Cannot send cash payment email: payment {payment_id} not found")
                return None

            return Message(
                subject="Cash Payment Submitted - South East Archers",
                recipients=[user.email],
                html=render_template(
                    "email/cash_payment_pending.html",
                    name=user.name,
                    reference=f"CASH-{payment.id}",
                    submitted_date=payment.created_at.strftime("%d %B %Y"),
                    description=payment.description,
                    amount=payment.amount,
                    instructions=SettingsService.get("cash_payment_instructions"),
                    payment_type=payment.payment_type,
                    history_url=MailService._safe_url_for("payment.history", "/payment/history"),
                ),
            )

        MailService._send(user_id, "cash payment pending email", _build)
