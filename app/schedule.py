from app import create_app
from app.scheduler import schedule
from app.scheduler.jobs import send_low_credits_reminder


def low_credits_reminder_job():
    """Wrapper for low credits reminder job with app context."""
    app = create_app()
    with app.app_context():
        send_low_credits_reminder()


schedule.call(low_credits_reminder_job, "Low credits reminder").weekly_on(1, "09:00")
