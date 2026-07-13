import logging

from app.core.config import get_settings
from app.repositories import MembershipRepository
from app.templating import templates, url_for
from app.utils.mail import send_email

logger = logging.getLogger(__name__)


def send_low_credits_reminder():
    memberships = MembershipRepository.get_active_for_active_users()
    low_credit_memberships = [m for m in memberships if m.credits_remaining() <= 3]

    if not low_credit_memberships:
        print("No members with low credits found")
        return

    print(f"Found {len(low_credit_memberships)} members with low credits")

    for membership in low_credit_memberships:
        user = membership.user
        if not user.email:
            print(f"Skipping user {user.id} - no email address")
            continue

        try:
            _send_reminder_email(user, membership.credits_remaining())
            print(f"✓ Sent low credits reminder to {user.email} ({membership.credits_remaining()} credits)")
        except Exception as e:
            print(f"✗ Failed to send email to {user.email}: {e}")


def _send_reminder_email(user, credits_remaining):
    try:
        credits_url = url_for("member.credits", _external=True)
    except Exception:
        credits_url = get_settings().app_url.rstrip("/") + "/member/credits"

    context = {"user": user, "credits_remaining": credits_remaining, "credits_url": credits_url}
    text_body = templates.env.get_template("email/low_credits_reminder.txt").render(**context)
    html_body = templates.env.get_template("email/low_credits_reminder.html").render(**context)
    send_email(
        "Low Credits Reminder - South East Archers",
        [user.email],
        text_body,
        html_body,
    )
