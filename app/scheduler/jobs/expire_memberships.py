"""Scheduled job to expire memberships on the configured membership year start date."""

from datetime import date

from app.services.membership_service import MembershipService
from app.services.settings_service import SettingsService


def expire_memberships():
    """Check if today is the membership year start date and expire initial credits if needed.

    This job runs daily at 00:01 GMT. If today matches the configured membership year
    start date (default: March 1st), it will expire initial credits for all expired
    memberships. This represents the start of a new membership year.
    """
    today = date.today()

    # Get configured membership year start date
    settings = SettingsService.get()
    start_month = settings.membership_year_start_month
    start_day = settings.membership_year_start_day

    # Check if today is the membership year start date
    if today.month == start_month and today.day == start_day:
        count = MembershipService.expire_memberships_for_year_end()
        print(f"Membership expiry: New year started, processed {count} expired memberships")
    else:
        print(f"Membership expiry: Not year start date (configured: {start_month}/{start_day}, today: {today.month}/{today.day})")
