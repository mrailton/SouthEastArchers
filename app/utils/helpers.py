from typing import Sequence

from flask_mail import Message

from app import mail


def send_email(
    subject: str,
    recipients: Sequence[str],
    text_body: str,
    html_body: str | None = None,
) -> None:
    """Send an email with optional HTML body."""
    msg = Message(subject, recipients=list(recipients))
    msg.body = text_body
    if html_body:
        msg.html = html_body

    mail.send(msg)
