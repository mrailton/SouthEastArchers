from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.enums import PaymentMethod
from app.services import settings
from app.templating import templates, url_for
from app.utils.mail import send_email

logger = logging.getLogger(__name__)

_PAYMENT_METHOD_LABELS = {
    PaymentMethod.ONLINE: "Credit/Debit Card (SumUp)",
    PaymentMethod.CASH: "Cash Payment",
}


def _render(template_name: str, **context: Any) -> str:
    return templates.env.get_template(template_name).render(**context)


def _safe_url_for(endpoint: str, fallback_path: str, **kwargs: Any) -> str:
    try:
        return url_for(endpoint, _external=True, **kwargs)
    except Exception:
        return get_settings().app_url.rstrip("/") + fallback_path


def _send(
    user_id: int,
    email_type: str,
    subject: str,
    recipients: list[str],
    html_template: str,
    text_template: str | None = None,
    **context: Any,
) -> None:
    from app.repositories import UserRepository

    try:
        user = UserRepository.get_by_id(user_id)
        if not user:
            logger.error("Cannot send %s: user %s not found", email_type, user_id)
            return
        context = {"user": user, **context}
        html_body = _render(html_template, **context)
        text_body = _render(text_template, **context) if text_template else ""
        send_email(subject, recipients or [user.email], text_body, html_body)
        logger.info("%s sent to %s", email_type.capitalize(), user.email)
    except Exception as exc:
        logger.error("Failed to send %s: %s", email_type, exc)


def send_password_reset(user_id: int, token: str) -> None:
    reset_url = _safe_url_for("auth.reset_password", f"/auth/reset-password/{token}", token=token)
    _send(
        user_id,
        "password reset email",
        "Reset Your Password - South East Archers",
        [],
        "email/reset_password.html",
        reset_url=reset_url,
    )


def send_payment_receipt(user_id: int, payment_id: int) -> None:
    from app.repositories import PaymentRepository, UserRepository

    user = UserRepository.get_by_id(user_id)
    payment = PaymentRepository.get_by_id(payment_id)
    if not user or not payment:
        logger.error("Cannot send receipt: user %s or payment %s not found", user_id, payment_id)
        return
    _send(
        user_id,
        "receipt email",
        "Payment Receipt - South East Archers",
        [user.email],
        "email/payment_receipt.html",
        "email/payment_receipt.txt",
        name=user.name,
        receipt_number=f"SEA-{payment.id:06d}",
        payment_date=payment.created_at.strftime("%d %B %Y at %H:%M"),
        description=payment.description or "Annual Membership",
        payment_method=_PAYMENT_METHOD_LABELS.get(payment.payment_method, str(payment.payment_method).title()),
        transaction_id=payment.external_transaction_id if payment.payment_method == PaymentMethod.ONLINE else None,
        amount=payment.amount,
        membership_start=user.membership.start_date.strftime("%d %B %Y") if user.membership else "",
        membership_expiry=user.membership.expiry_date.strftime("%d %B %Y") if user.membership else "",
        credits=user.membership.credits_remaining() if user.membership else 0,
        login_url=_safe_url_for("auth.login", "/auth/login"),
    )


def send_credit_purchase_receipt(user_id: int, payment_id: int, credits_purchased: int) -> None:
    from app.repositories import PaymentRepository, UserRepository

    user = UserRepository.get_by_id(user_id)
    payment = PaymentRepository.get_by_id(payment_id)
    if not user or not payment:
        logger.error("Cannot send credit receipt: user %s or payment %s not found", user_id, payment_id)
        return
    _send(
        user_id,
        "credit receipt email",
        "Credit Purchase Receipt - South East Archers",
        [user.email],
        "email/credit_receipt.html",
        "email/credit_receipt.txt",
        name=user.name,
        receipt_number=f"SEA-{payment.id:06d}",
        payment_date=payment.created_at.strftime("%d %B %Y at %H:%M"),
        description=payment.description or f"{credits_purchased} shooting credits",
        payment_method=_PAYMENT_METHOD_LABELS.get(payment.payment_method, str(payment.payment_method).title()),
        transaction_id=payment.external_transaction_id if payment.payment_method == PaymentMethod.ONLINE else None,
        amount=payment.amount,
        credits_purchased=credits_purchased,
        credits_remaining=user.membership.credits_remaining() if user.membership else 0,
        login_url=_safe_url_for("member.credits", "/member/credits"),
    )


def send_welcome_email(user_id: int) -> None:
    _send(
        user_id,
        "welcome email",
        "Welcome to South East Archers!",
        [],
        "email/welcome.html",
        "email/welcome.txt",
        login_url=_safe_url_for("auth.login", "/auth/login"),
        membership_cost=settings.get("annual_membership_cost"),
        credits_included=settings.get("membership_shoots_included"),
    )


def send_new_member_notification(new_user_id: int) -> None:
    from app.repositories import UserRepository

    new_user = UserRepository.get_by_id(new_user_id)
    if not new_user:
        return
    admin_users = UserRepository.get_all_with_permission("members.manage_membership")
    if not admin_users:
        return
    try:
        send_email(
            f"New Member Sign-Up: {new_user.name} - South East Archers",
            [u.email for u in admin_users],
            _render(
                "email/new_member_notification.txt",
                new_member_name=new_user.name,
                new_member_email=new_user.email,
                new_member_phone=new_user.phone,
                new_member_qualification=new_user.qualification,
                admin_url=_safe_url_for("admin.members", "/admin/members"),
            ),
            _render(
                "email/new_member_notification.html",
                new_member_name=new_user.name,
                new_member_email=new_user.email,
                new_member_phone=new_user.phone,
                new_member_qualification=new_user.qualification,
                admin_url=_safe_url_for("admin.members", "/admin/members"),
            ),
        )
        logger.info("New member notification sent for user %s", new_user.email)
    except Exception as exc:
        logger.error("Failed to send new member notification: %s", exc)


def send_cash_payment_pending_email(user_id: int, payment_id: int) -> None:
    from app.repositories import PaymentRepository, UserRepository

    user = UserRepository.get_by_id(user_id)
    payment = PaymentRepository.get_by_id(payment_id)
    if not user or not payment:
        logger.error("Cannot send cash payment email: user %s or payment %s not found", user_id, payment_id)
        return
    _send(
        user_id,
        "cash payment pending email",
        "Cash Payment Submitted - South East Archers",
        [user.email],
        "email/cash_payment_pending.html",
        name=user.name,
        reference=f"CASH-{payment.id}",
        submitted_date=payment.created_at.strftime("%d %B %Y"),
        description=payment.description,
        amount=payment.amount,
        instructions=settings.get("cash_payment_instructions"),
        payment_type=payment.payment_type,
        history_url=_safe_url_for("payment.history", "/payment/history"),
    )
