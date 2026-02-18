"""Tests for scheduled jobs."""

from datetime import date, timedelta
from unittest.mock import patch

from app import db
from app.models import Membership, User
from app.scheduler.jobs import expire_memberships, send_low_credits_reminder

# Expire memberships tests

def test_expire_memberships_on_start_date(app):
    """Test that memberships are expired on the year start date"""
    from app.models import ApplicationSettings
    from app.services.membership_service import MembershipService

    with app.app_context():
        # Set today as start date
        today = date.today()
        settings = ApplicationSettings.query.first()
        if not settings:
            settings = ApplicationSettings()
            db.session.add(settings)
        settings.membership_year_start_month = today.month
        settings.membership_year_start_day = today.day
        db.session.commit()

        with patch.object(MembershipService, "expire_memberships_for_year_end", return_value=5) as mock_expire:
            expire_memberships()
            assert mock_expire.called


def test_expire_memberships_skipped_on_other_dates(app):
    """Test that memberships are not expired on other dates"""
    from app.models import ApplicationSettings
    from app.services.membership_service import MembershipService

    with app.app_context():
        # Set start date to tomorrow
        tomorrow = date.today() + timedelta(days=1)
        settings = ApplicationSettings.query.first()
        if not settings:
            settings = ApplicationSettings()
            db.session.add(settings)
        settings.membership_year_start_month = tomorrow.month
        settings.membership_year_start_day = tomorrow.day
        db.session.commit()

        with patch.object(MembershipService, "expire_memberships_for_year_end") as mock_expire:
            expire_memberships()
            assert not mock_expire.called


# Low credits reminder tests

def test_low_credits_reminder_sends_to_members_with_3_credits(app):
    """Test that emails are sent to members with 3 credits"""
    user = User(name="Test User", email="test@example.com", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=3,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert mock_mail.send.called
        sent_message = mock_mail.send.call_args[0][0]
        assert sent_message.recipients == ["test@example.com"]
        assert "Low Credits" in sent_message.subject
        assert "3" in sent_message.body


def test_low_credits_reminder_sends_to_members_with_1_credit(app):
    """Test that emails are sent to members with 1 credit"""
    user = User(name="Low Credit User", email="lowcredit@example.com", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=1,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert mock_mail.send.called
        sent_message = mock_mail.send.call_args[0][0]
        assert sent_message.recipients == ["lowcredit@example.com"]


def test_low_credits_reminder_sends_to_members_with_0_credits(app):
    """Test that emails are sent to members with 0 credits"""
    user = User(name="Zero Credit User", email="zero@example.com", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=0,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert mock_mail.send.called


def test_low_credits_reminder_skips_members_with_more_credits(app):
    """Test that no emails are sent to members with more than 3 credits"""
    user = User(name="High Credit User", email="high@example.com", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=10,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert not mock_mail.send.called


def test_low_credits_reminder_skips_inactive_memberships(app):
    """Test that no emails are sent to inactive memberships"""
    user = User(name="Inactive User", email="inactive@example.com", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=2,
        purchased_credits=0,
        status="pending",  # Not active
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert not mock_mail.send.called


def test_low_credits_reminder_skips_inactive_users(app):
    """Test that no emails are sent to inactive users"""
    user = User(name="Inactive User", email="inactive@example.com", is_active=False)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=2,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert not mock_mail.send.called


def test_low_credits_reminder_sends_to_multiple_members(app):
    """Test that emails are sent to all qualifying members"""
    for i in range(3):
        user = User(name=f"User {i}", email=f"user{i}@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            initial_credits=i + 1,  # 1, 2, 3 credits
            purchased_credits=0,
            status="active",
        )
        db.session.add(membership)

    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert mock_mail.send.call_count == 3


def test_low_credits_reminder_skips_users_without_email(app):
    """Test that users with empty email addresses are skipped gracefully"""
    user = User(name="No Email User", email="", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=2,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert not mock_mail.send.called


def test_low_credits_reminder_continues_on_email_failure(app):
    """Test that job continues if one email fails"""
    for i in range(2):
        user = User(name=f"User {i}", email=f"user{i}@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            initial_credits=2,
            purchased_credits=0,
            status="active",
        )
        db.session.add(membership)

    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        mock_mail.send.side_effect = [Exception("Email failed"), None]

        send_low_credits_reminder()

        assert mock_mail.send.call_count == 2


def test_low_credits_reminder_handles_negative_credits(app):
    """Test that emails are sent to members with negative credits"""
    user = User(name="Negative Credit User", email="negative@example.com", is_active=True)
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=300),
        initial_credits=-2,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
        send_low_credits_reminder()

        assert mock_mail.send.called
        call_args = mock_mail.send.call_args[0][0]
        assert "-2" in call_args.html or "negative" in call_args.html.lower()
