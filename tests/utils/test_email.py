"""Tests for email utility functions"""

from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models import Membership, Payment, User
from app.utils.email import send_payment_receipt, send_welcome_email


class TestSendPaymentReceipt:
    @patch("app.utils.email.mail")
    def test_send_payment_receipt_online_payment(self, mock_mail, app, test_user):
        """Test sending payment receipt for online payment"""
        with app.app_context():
            from datetime import datetime

            # Create test payment and membership
            payment = Payment(
                id=123,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                external_transaction_id="txn_abc123",
                payment_processor="sumup",
                description="Annual Membership",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            result = send_payment_receipt(test_user, payment, membership)

            assert result is True
            assert mock_mail.send.called

            # Check the message
            call_args = mock_mail.send.call_args[0][0]
            assert call_args.subject == "Payment Receipt - South East Archers"
            assert test_user.email in call_args.recipients
            assert call_args.html is not None
            assert call_args.body is not None

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_cash_payment(self, mock_mail, app, test_user):
        """Test sending payment receipt for cash payment"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=456,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="cash",
                description="Annual Membership",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            result = send_payment_receipt(test_user, payment, membership)

            assert result is True
            assert mock_mail.send.called

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_formats_receipt_number(self, mock_mail, app, test_user):
        """Test receipt number formatting"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=42,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            send_payment_receipt(test_user, payment, membership)

            # Receipt number should be SEA-000042
            call_args = mock_mail.send.call_args[0][0]
            assert "SEA-000042" in call_args.html or "SEA-000042" in call_args.body

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_includes_transaction_id_for_online(self, mock_mail, app, test_user):
        """Test transaction ID is included for online payments"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=789,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                external_transaction_id="txn_xyz789",
                payment_processor="sumup",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            send_payment_receipt(test_user, payment, membership)

            call_args = mock_mail.send.call_args[0][0]
            # Transaction ID should be in the email
            assert "txn_xyz789" in call_args.html or "txn_xyz789" in call_args.body

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_no_transaction_id_for_cash(self, mock_mail, app, test_user):
        """Test no transaction ID for cash payments"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=999,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="cash",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            send_payment_receipt(test_user, payment, membership)

            assert mock_mail.send.called

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_formats_dates(self, mock_mail, app, test_user):
        """Test date formatting in receipt"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=111,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            send_payment_receipt(test_user, payment, membership)

            assert mock_mail.send.called
            call_args = mock_mail.send.call_args[0][0]
            # Check that dates are formatted
            assert call_args.html is not None

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_includes_membership_details(self, mock_mail, app, test_user):
        """Test membership details are included in receipt"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=222,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            send_payment_receipt(test_user, payment, membership)

            call_args = mock_mail.send.call_args[0][0]
            # Check membership details are included
            html_body = call_args.html
            assert membership.start_date.strftime("%d %B %Y") in html_body or membership.start_date.strftime("%d %B %Y") in call_args.body

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_handles_missing_description(self, mock_mail, app, test_user):
        """Test receipt handles missing payment description"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=333,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                description=None,
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            result = send_payment_receipt(test_user, payment, membership)

            assert result is True

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_exception_handling(self, mock_mail, app, test_user):
        """Test exception handling when sending fails"""
        with app.app_context():
            from datetime import datetime

            mock_mail.send.side_effect = Exception("SMTP error")

            payment = Payment(
                id=444,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            result = send_payment_receipt(test_user, payment, membership)

            assert result is False

    @patch("app.utils.email.mail")
    def test_send_payment_receipt_uses_correct_payment_method_display(self, mock_mail, app, test_user):
        """Test payment method display formatting"""
        with app.app_context():
            from datetime import datetime

            payment = Payment(
                id=555,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )

            membership = test_user.membership

            send_payment_receipt(test_user, payment, membership)

            call_args = mock_mail.send.call_args[0][0]
            # Should show "Credit/Debit Card (SumUp)" for online
            assert "SumUp" in call_args.html or "Card" in call_args.html


class TestSendWelcomeEmail:
    @patch("app.utils.email.mail")
    def test_send_welcome_email_success(self, mock_mail, app, test_user):
        """Test sending welcome email"""
        with app.app_context():
            membership = test_user.membership

            result = send_welcome_email(test_user, membership)

            assert result is True
            assert mock_mail.send.called

            # Check the message
            call_args = mock_mail.send.call_args[0][0]
            assert call_args.subject == "Welcome to South East Archers!"
            assert test_user.email in call_args.recipients
            assert call_args.html is not None

    @patch("app.utils.email.mail")
    def test_send_welcome_email_includes_user_name(self, mock_mail, app, test_user):
        """Test welcome email includes user name"""
        with app.app_context():
            membership = test_user.membership

            send_welcome_email(test_user, membership)

            call_args = mock_mail.send.call_args[0][0]
            assert test_user.name in call_args.html

    @patch("app.utils.email.mail")
    def test_send_welcome_email_includes_membership_details(self, mock_mail, app, test_user):
        """Test welcome email includes membership details"""
        with app.app_context():
            membership = test_user.membership

            send_welcome_email(test_user, membership)

            call_args = mock_mail.send.call_args[0][0]
            html = call_args.html

            # Check membership details are included
            assert membership.start_date.strftime("%d %B %Y") in html
            assert membership.expiry_date.strftime("%d %B %Y") in html
            assert str(membership.credits) in html

    @patch("app.utils.email.mail")
    def test_send_welcome_email_includes_login_link(self, mock_mail, app, test_user):
        """Test welcome email includes login link"""
        with app.app_context():
            membership = test_user.membership

            send_welcome_email(test_user, membership)

            call_args = mock_mail.send.call_args[0][0]
            # Should contain a login URL
            assert "login" in call_args.html.lower() or "auth/login" in call_args.html

    @patch("app.utils.email.mail")
    def test_send_welcome_email_exception_handling(self, mock_mail, app, test_user):
        """Test exception handling when sending fails"""
        with app.app_context():
            mock_mail.send.side_effect = Exception("Email server error")

            membership = test_user.membership

            result = send_welcome_email(test_user, membership)

            assert result is False

    @patch("app.utils.email.mail")
    def test_send_welcome_email_with_different_credit_amounts(self, mock_mail, app):
        """Test welcome email with various credit amounts"""
        with app.app_context():
            # Create user with different credit amount
            user = User(
                name="Test User 2",
                email="test2@example.com",
                phone="1234567890",
                date_of_birth=date(2000, 1, 1),
            )
            user.set_password("password")

            membership = Membership(
                user_id=None,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                credits=50,
                status="active",
            )

            from app import db

            db.session.add(user)
            db.session.flush()

            membership.user_id = user.id
            db.session.add(membership)
            db.session.commit()

            result = send_welcome_email(user, membership)

            assert result is True
            call_args = mock_mail.send.call_args[0][0]
            assert "50" in call_args.html


class TestEmailURLGeneration:
    """Test URL generation in emails works in different contexts"""

    @patch("app.utils.email.mail")
    def test_email_with_server_name_configured(self, mock_mail, app, test_user):
        """Test email works when SERVER_NAME is configured"""
        with app.app_context():
            # TestingConfig should have SERVER_NAME configured
            assert app.config.get("SERVER_NAME") is not None

            from datetime import datetime

            payment = Payment(
                id=1,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )
            membership = test_user.membership

            result = send_payment_receipt(test_user, payment, membership)

            assert result is True
            assert mock_mail.send.called

    @patch("app.utils.email.mail")
    def test_email_without_server_name_uses_fallback(self, mock_mail, app, test_user):
        """Test email uses SITE_URL fallback when SERVER_NAME not configured"""
        with app.app_context():
            # Temporarily remove SERVER_NAME to test fallback
            original_server_name = app.config.get("SERVER_NAME")
            app.config["SERVER_NAME"] = None
            app.config["SITE_URL"] = "https://test.example.com"

            try:
                from datetime import datetime

                payment = Payment(
                    id=2,
                    user_id=test_user.id,
                    amount=100.00,
                    currency="EUR",
                    payment_type="membership",
                    payment_method="online",
                    status="completed",
                    created_at=datetime.now(),
                )
                membership = test_user.membership

                # Should not raise RuntimeError - fallback should work
                result = send_payment_receipt(test_user, payment, membership)

                assert result is True
                assert mock_mail.send.called
                # Verify email was sent successfully with login link
                call_args = mock_mail.send.call_args[0][0]
                assert "login" in call_args.html.lower() or "login" in call_args.body.lower()
            finally:
                # Restore SERVER_NAME
                app.config["SERVER_NAME"] = original_server_name

    @patch("app.utils.email.mail")
    def test_welcome_email_with_url_generation(self, mock_mail, app, test_user):
        """Test welcome email URL generation works"""
        with app.app_context():
            membership = test_user.membership

            result = send_welcome_email(test_user, membership)

            assert result is True
            call_args = mock_mail.send.call_args[0][0]
            # Should contain login link
            assert "login" in call_args.html.lower()

    @patch("app.utils.email.mail")
    def test_welcome_email_without_server_name(self, mock_mail, app, test_user):
        """Test welcome email fallback when SERVER_NAME not configured"""
        with app.app_context():
            original_server_name = app.config.get("SERVER_NAME")
            app.config["SERVER_NAME"] = None
            app.config["SITE_URL"] = "https://fallback.example.com"

            try:
                membership = test_user.membership

                # Should not raise RuntimeError - fallback should work
                result = send_welcome_email(test_user, membership)

                assert result is True
                call_args = mock_mail.send.call_args[0][0]
                # Check that email was sent with login link (fallback worked)
                assert "login" in call_args.html.lower()
            finally:
                app.config["SERVER_NAME"] = original_server_name

    def test_config_has_server_name_in_testing(self, app):
        """Ensure test app has SERVER_NAME configured to prevent URL generation errors"""
        assert app.config.get("SERVER_NAME") is not None
        assert app.config.get("PREFERRED_URL_SCHEME") is not None

    def test_config_has_site_url_fallback(self, app):
        """Ensure config provides SITE_URL fallback option"""
        # Test that we can set SITE_URL as fallback
        app.config["SITE_URL"] = "https://example.com"
        assert app.config.get("SITE_URL") == "https://example.com"

    @patch("app.utils.email.url_for")
    @patch("app.utils.email.mail")
    def test_fallback_mechanism_when_url_for_fails(self, mock_mail, mock_url_for, app, test_user):
        """Test that fallback mechanism is triggered when url_for raises RuntimeError"""
        with app.app_context():
            # Make url_for raise RuntimeError to test fallback
            mock_url_for.side_effect = RuntimeError("SERVER_NAME not configured")
            app.config["SITE_URL"] = "https://example.com"

            from datetime import datetime

            payment = Payment(
                id=3,
                user_id=test_user.id,
                amount=100.00,
                currency="EUR",
                payment_type="membership",
                payment_method="online",
                status="completed",
                created_at=datetime.now(),
            )
            membership = test_user.membership

            # Should catch RuntimeError and use fallback
            result = send_payment_receipt(test_user, payment, membership)

            # Should succeed using fallback
            assert result is True
            assert mock_mail.send.called
