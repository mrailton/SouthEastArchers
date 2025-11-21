from flask_mail import Message
from flask import current_app
from app import mail


def send_email(subject, recipients, text_body, html_body=None):
    """Send email"""
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body

    mail.send(msg)
