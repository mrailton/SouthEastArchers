from collections.abc import Sequence

from flask import request
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


def parse_visitors_from_form() -> list[dict]:
    names = request.form.getlist("visitor_name")
    clubs = request.form.getlist("visitor_club")
    affiliations = request.form.getlist("visitor_affiliation")
    payment_methods = request.form.getlist("visitor_payment_method")

    visitors = []
    for i in range(len(names)):
        name = names[i].strip() if i < len(names) else ""
        club = clubs[i].strip() if i < len(clubs) else ""
        affiliation = affiliations[i] if i < len(affiliations) else ""
        payment_method = payment_methods[i] if i < len(payment_methods) else ""
        if name and club and affiliation and payment_method:
            visitors.append(
                {
                    "name": name,
                    "club": club,
                    "affiliation": affiliation,
                    "payment_method": payment_method,
                }
            )
    return visitors
