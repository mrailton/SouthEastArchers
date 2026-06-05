from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app import db
from app.models import Membership, User
from app.scheduler.jobs import expire_memberships, send_low_credits_reminder

# Expire memberships tests


def test_expire_memberships_on_start_date(app):
    """Test that memberships are expired on the year start date"""
    from app.services.membership_service import MembershipService
    from app.services.settings_service import SettingsService

    with app.app_context():
        today = date.today()
        SettingsService.set("membership_year_start_month", today.month)
        SettingsService.set("membership_year_start_day", today.day)

        with patch.object(MembershipService, "expire_memberships_for_year_end", return_value=5) as mock_expire:
            expire_memberships()
            assert mock_expire.called


def test_expire_memberships_skipped_on_other_dates(app):
    """Test that memberships are not expired on other dates"""
    from app.services.membership_service import MembershipService
    from app.services.settings_service import SettingsService

    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        SettingsService.set("membership_year_start_month", tomorrow.month)
        SettingsService.set("membership_year_start_day", tomorrow.day)

        with patch.object(MembershipService, "expire_memberships_for_year_end") as mock_expire:
            expire_memberships()
            assert not mock_expire.called


def _create_member(email, initial_credits=2, status="active", is_active=True):
    """Helper to create a member with membership for low credit tests."""
    user = User(name=email.split("@")[0] if email else "NoEmail", email=email, is_active=is_active)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=initial_credits,
        purchased_credits=0,
        status=status,
    )
    db.session.add(membership)
    db.session.commit()
    return user


@pytest.mark.parametrize(
    "status,is_active,email",
    [
        ("pending", True, "pending_membership@example.com"),
        (None, False, "inactive_user@example.com"),
        (None, True, ""),
    ],
)
def test_low_credits_reminder_skips_invalid(app, status, is_active, email):
    """Test that reminders are skipped for invalid memberships/users."""
    _create_member(email, status=status or "active", is_active=is_active)

    with patch("app.scheduler.jobs.low_credits_reminder.send_email") as mock_send:
        send_low_credits_reminder()
        assert not mock_send.called


def test_low_credits_reminder_handles_negative_credits(app):
    """Test that emails are sent to members with negative credits."""
    _create_member("negative@example.com", initial_credits=-2)

    with patch("app.scheduler.jobs.low_credits_reminder.send_email") as mock_send:
        send_low_credits_reminder()
        assert mock_send.called
        html_body = mock_send.call_args[0][3]
        assert "-2" in html_body or "negative" in html_body.lower()


def test_low_credits_reminder_sends_to_multiple_members(app):
    """Test that emails are sent to all qualifying members."""
    for i in range(3):
        _create_member(f"user{i}@example.com", initial_credits=i + 1)

    with patch("app.scheduler.jobs.low_credits_reminder.send_email") as mock_send:
        send_low_credits_reminder()
        assert mock_send.call_count == 3


def test_low_credits_reminder_continues_on_email_failure(app):
    """Test that job continues if one email fails."""
    for i in range(2):
        _create_member(f"fail_user{i}@example.com", initial_credits=2)

    with patch("app.scheduler.jobs.low_credits_reminder.send_email") as mock_send:
        mock_send.side_effect = [Exception("Email failed"), None]
        send_low_credits_reminder()
        assert mock_send.call_count == 2
