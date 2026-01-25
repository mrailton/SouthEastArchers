from flask import current_app, render_template, url_for
from flask_mail import Message

from app import mail
from app.models import Membership, User


def send_low_credits_reminder():
    # Find active memberships with 3 or fewer total credits (initial + purchased)
    memberships = Membership.query.filter(Membership.status == "active").join(User).filter(User.is_active).all()
    low_credit_memberships = [m for m in memberships if m.credits_remaining() <= 3]

    if not low_credit_memberships:
        print("No members with low credits found")
        return

    print(f"Found {len(low_credit_memberships)} members with low credits")

    for membership in low_credit_memberships:
        user = membership.user

        # Skip if user doesn't have an email
        if not user.email:
            print(f"Skipping user {user.id} - no email address")
            continue

        try:
            _send_reminder_email(user, membership.credits_remaining())
            print(f"✓ Sent low credits reminder to {user.email} ({membership.credits_remaining()} credits)")
        except Exception as e:
            print(f"✗ Failed to send email to {user.email}: {e}")


def _send_reminder_email(user, credits_remaining):
    # Generate URL for purchasing credits
    try:
        credits_url = url_for("member.credits", _external=True)
    except RuntimeError:
        # Fallback if outside request context
        credits_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/member/credits"

    # Prepare template data
    template_data = {"user": user, "credits_remaining": credits_remaining, "credits_url": credits_url}

    # Create and send the email
    msg = Message(
        "Low Credits Reminder - South East Archers",
        recipients=[user.email],
        body=render_template("email/low_credits_reminder.txt", **template_data),
        html=render_template("email/low_credits_reminder.html", **template_data),
    )

    mail.send(msg)
