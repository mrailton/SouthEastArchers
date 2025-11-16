from flask_mail import Message
from flask import current_app
from app import mail, db


def send_email(subject, recipients, text_body, html_body=None):
    """Send email"""
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body

    mail.send(msg)


def get_user_or_404(user_id):
    """Get user by ID or return 404"""
    from app.models import User
    user = db.session.get(User, user_id)
    if not user:
        from flask import abort
        abort(404)
    return user
