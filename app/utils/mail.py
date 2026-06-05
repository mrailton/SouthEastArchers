from __future__ import annotations

import logging
import smtplib
from collections.abc import Sequence
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(
    subject: str,
    recipients: Sequence[str],
    text_body: str,
    html_body: str | None = None,
) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.mail_default_sender
    message["To"] = ", ".join(recipients)
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        if settings.mail_use_ssl:
            with smtplib.SMTP_SSL(settings.mail_server, settings.mail_port) as smtp:
                if settings.mail_username and settings.mail_password:
                    smtp.login(settings.mail_username, settings.mail_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.mail_server, settings.mail_port) as smtp:
                if settings.mail_use_tls:
                    smtp.starttls()
                if settings.mail_username and settings.mail_password:
                    smtp.login(settings.mail_username, settings.mail_password)
                smtp.send_message(message)
    except Exception:
        logger.exception("Failed to send email to %s", recipients)
