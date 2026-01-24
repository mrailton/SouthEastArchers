"""Tests for scheduled jobs."""

from datetime import date, timedelta
from unittest.mock import patch

from app import db
from app.models import Membership, User
from app.scheduler.jobs import send_low_credits_reminder


class TestLowCreditsReminder:
    """Test the low credits reminder job."""

    def test_sends_email_to_members_with_3_credits(self, app):
        """Test that emails are sent to members with 3 credits"""
        # Create a user with active membership and 3 credits
        user = User(name="Test User", email="test@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=3,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        # Mock mail.send
        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            # Verify email was sent
            assert mock_mail.send.called
            sent_message = mock_mail.send.call_args[0][0]
            assert sent_message.recipients == ["test@example.com"]
            assert "Low Credits" in sent_message.subject
            assert "3" in sent_message.body

    def test_sends_email_to_members_with_1_credit(self, app):
        """Test that emails are sent to members with 1 credit"""
        user = User(name="Low Credit User", email="lowcredit@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=1,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            assert mock_mail.send.called
            sent_message = mock_mail.send.call_args[0][0]
            assert sent_message.recipients == ["lowcredit@example.com"]

    def test_sends_email_to_members_with_0_credits(self, app):
        """Test that emails are sent to members with 0 credits"""
        user = User(name="Zero Credit User", email="zero@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=0,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            assert mock_mail.send.called

    def test_does_not_send_to_members_with_more_credits(self, app):
        """Test that no emails are sent to members with more than 3 credits"""
        user = User(name="High Credit User", email="high@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=10,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            # Should not send email
            assert not mock_mail.send.called

    def test_does_not_send_to_inactive_memberships(self, app):
        """Test that no emails are sent to inactive memberships"""
        user = User(name="Inactive User", email="inactive@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=2,
            status="pending",  # Not active
        )
        db.session.add(membership)
        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            assert not mock_mail.send.called

    def test_does_not_send_to_inactive_users(self, app):
        """Test that no emails are sent to inactive users"""
        user = User(name="Inactive User", email="inactive@example.com", is_active=False)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=2,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            assert not mock_mail.send.called

    def test_sends_to_multiple_members(self, app):
        """Test that emails are sent to all qualifying members"""
        # Create 3 users with low credits
        for i in range(3):
            user = User(name=f"User {i}", email=f"user{i}@example.com", is_active=True)
            user.set_password("password")
            db.session.add(user)
            db.session.flush()

            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=300),
                credits=i + 1,  # 1, 2, 3 credits
                status="active",
            )
            db.session.add(membership)

        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            # Should have sent 3 emails
            assert mock_mail.send.call_count == 3

    def test_handles_users_without_email(self, app):
        """Test that users with empty email addresses are skipped gracefully"""
        user = User(name="No Email User", email="", is_active=True)  # Empty string instead of None
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=2,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        # Should not raise an error
        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            # Should not send email
            assert not mock_mail.send.called

    def test_continues_on_email_failure(self, app):
        """Test that job continues if one email fails"""
        # Create 2 users with low credits
        for i in range(2):
            user = User(name=f"User {i}", email=f"user{i}@example.com", is_active=True)
            user.set_password("password")
            db.session.add(user)
            db.session.flush()

            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=300),
                credits=2,
                status="active",
            )
            db.session.add(membership)

        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            # Make first email fail
            mock_mail.send.side_effect = [Exception("Email failed"), None]

            # Should not raise, should continue
            send_low_credits_reminder()

            # Should have attempted both emails
            assert mock_mail.send.call_count == 2

    def test_sends_email_to_members_with_negative_credits(self, app):
        """Test that emails are sent to members with negative credits"""
        user = User(name="Negative Credit User", email="negative@example.com", is_active=True)
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=300),
            credits=-2,  # Negative credits
            status="active",
        )
        db.session.add(membership)
        db.session.commit()

        with patch("app.scheduler.jobs.low_credits_reminder.mail") as mock_mail:
            send_low_credits_reminder()

            # Should send email even with negative credits
            assert mock_mail.send.called
            # Verify the email shows the correct negative number
            call_args = mock_mail.send.call_args[0][0]
            assert "-2" in call_args.html or "negative" in call_args.html.lower()
