from app import create_app
from app.scheduler import schedule
from app.scheduler.jobs import expire_memberships, send_low_credits_reminder


def low_credits_reminder_job():
    """Wrapper for low credits reminder job with app context."""
    app = create_app()
    with app.app_context():
        send_low_credits_reminder()


def expire_memberships_job():
    """Wrapper for membership expiry job with app context."""
    app = create_app()
    with app.app_context():
        expire_memberships()


schedule.call(low_credits_reminder_job, "Low credits reminder").weekly_on(1, "09:00")
schedule.call(expire_memberships_job, "Expire memberships").daily_at("00:01")
