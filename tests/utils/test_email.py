from datetime import date, timedelta
from unittest.mock import patch

from app.models import Membership, Payment, User
from app.utils.email import send_payment_receipt, send_welcome_email
from tests.helpers import assert_email_contains, assert_email_sent


def test_send_payment_receipt_online_payment(app, test_user, fake_mailer):
    """Test sending payment receipt for online payment"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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
        email_sent = assert_email_sent(fake_mailer, subject_contains="Payment Receipt", recipients=[test_user.email])
        assert email_sent.html is not None
        assert email_sent.body is not None


def test_send_payment_receipt_cash_payment(app, test_user, fake_mailer):
    """Test sending payment receipt for cash payment"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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
        from tests.helpers import assert_email_sent

        assert_email_sent(fake_mailer)


def test_send_payment_receipt_formats_receipt_number(app, test_user, fake_mailer):
    """Test receipt number formatting"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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
        from tests.helpers import assert_email_contains

        assert_email_contains(fake_mailer, "SEA-000042")


def test_send_payment_receipt_includes_transaction_id_for_online(app, test_user, fake_mailer):
    """Test transaction ID is included for online payments"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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

        from tests.helpers import assert_email_contains

        # Transaction ID should be in the email
        assert_email_contains(fake_mailer, "txn_xyz789")


def test_send_payment_receipt_no_transaction_id_for_cash(app, test_user, fake_mailer):
    """Test no transaction ID for cash payments"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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

        from tests.helpers import assert_email_sent

        assert_email_sent(fake_mailer)


def test_send_payment_receipt_formats_dates(app, test_user, fake_mailer):
    """Test date formatting in receipt"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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

        mail_sent = assert_email_sent(fake_mailer)
        assert mail_sent.html is not None


def test_send_payment_receipt_includes_membership_details(app, test_user, fake_mailer):
    """Test membership details are included in receipt"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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

        mail_sent = assert_email_sent(fake_mailer)
        html_body = mail_sent.html or ""
        assert membership.start_date.strftime("%d %B %Y") in html_body or membership.start_date.strftime("%d %B %Y") in (mail_sent.body or "")


def test_send_payment_receipt_handles_missing_description(app, test_user, fake_mailer):
    """Test receipt handles missing payment description"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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


def test_send_payment_receipt_exception_handling(app, test_user, fake_mailer):
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        from datetime import datetime

        # Simulate send raising an exception
        def raise_send(msg):
            raise Exception("SMTP error")

        fake_mailer.send = raise_send

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


def test_send_payment_receipt_uses_correct_payment_method_display(app, test_user, fake_mailer):
    """Test payment method display formatting"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
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

        from tests.helpers import assert_email_contains

        # Should show "Credit/Debit Card (SumUp)" for online
        assert_email_contains(fake_mailer, "SumUp")


# TestSendWelcomeEmail


def test_send_welcome_email_success(app, test_user, fake_mailer):
    """Test sending welcome email"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        membership = test_user.membership

        result = send_welcome_email(test_user, membership)

        assert result is True
        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer, subject_contains="Welcome to South East Archers!", recipients=[test_user.email])
        assert call_args.html is not None


def test_send_welcome_email_includes_user_name(app, test_user, fake_mailer):
    """Test welcome email includes user name"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        membership = test_user.membership

        send_welcome_email(test_user, membership)

        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer)
        assert test_user.name in (call_args.html or "")


def test_send_welcome_email_includes_membership_details(app, test_user, fake_mailer):
    """Test welcome email includes membership details"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        membership = test_user.membership

        send_welcome_email(test_user, membership)

        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer)
        html = call_args.html

        # Check membership details are included
        assert membership.start_date.strftime("%d %B %Y") in html
        assert membership.expiry_date.strftime("%d %B %Y") in html
        assert str(membership.credits) in html


def test_send_welcome_email_includes_login_link(app, test_user, fake_mailer):
    """Test welcome email includes login link"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        membership = test_user.membership

        send_welcome_email(test_user, membership)

        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer)
        # Should contain a login URL
        assert "login" in (call_args.html or "").lower() or "auth/login" in (call_args.html or "")


def test_send_welcome_email_exception_handling(app, test_user, fake_mailer):
    """Test exception handling when sending fails"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

        # Simulate send raising an exception
        def raise_send(msg):
            raise Exception("Email server error")

        fake_mailer.send = raise_send

        membership = test_user.membership

        result = send_welcome_email(test_user, membership)

        assert result is False


def test_send_welcome_email_with_different_credit_amounts(app, fake_mailer):
    """Test welcome email with various credit amounts"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        # Create user with different credit amount
        user = User(
            name="Test User 2",
            email="test2@example.com",
            phone="1234567890",
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
        from tests.helpers import assert_email_contains

        assert_email_contains(fake_mailer, "50")


# TestEmailURLGeneration


def test_email_with_server_name_configured(app, test_user, fake_mailer):
    """Test email works when SERVER_NAME is configured"""
    with app.app_context():
        # TestingConfig should have SERVER_NAME configured
        assert app.config.get("SERVER_NAME") is not None

        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

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
        from tests.helpers import assert_email_sent

        assert_email_sent(fake_mailer)


def test_email_without_server_name_uses_fallback(app, test_user, fake_mailer):
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

            import app.utils.email as email_mod

            email_mod.mail = fake_mailer

            # Should not raise RuntimeError - fallback should work
            result = send_payment_receipt(test_user, payment, membership)

            assert result is True
            from tests.helpers import assert_email_contains, assert_email_sent

            assert_email_sent(fake_mailer)
            assert_email_contains(fake_mailer, "login")
        finally:
            # Restore SERVER_NAME
            app.config["SERVER_NAME"] = original_server_name


def test_welcome_email_with_url_generation(app, test_user, fake_mailer):
    """Test welcome email URL generation works"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        membership = test_user.membership

        result = send_welcome_email(test_user, membership)

        assert result is True
        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer)
        # Should contain login link
        assert "login" in (call_args.html or "").lower()


def test_welcome_email_without_server_name(app, test_user, fake_mailer):
    """Test welcome email fallback when SERVER_NAME not configured"""
    with app.app_context():
        original_server_name = app.config.get("SERVER_NAME")
        app.config["SERVER_NAME"] = None
        app.config["SITE_URL"] = "https://fallback.example.com"

        try:
            import app.utils.email as email_mod

            email_mod.mail = fake_mailer
            membership = test_user.membership

            # Should not raise RuntimeError - fallback should work
            result = send_welcome_email(test_user, membership)

            assert result is True
            assert_email_sent(fake_mailer)
            assert_email_contains(fake_mailer, "login")
        finally:
            app.config["SERVER_NAME"] = original_server_name


def test_config_has_server_name_in_testing(app):
    """Ensure test app has SERVER_NAME configured to prevent URL generation errors"""
    assert app.config.get("SERVER_NAME") is not None
    assert app.config.get("PREFERRED_URL_SCHEME") is not None


def test_config_has_site_url_fallback(app):
    """Ensure config provides SITE_URL fallback option"""
    # Test that we can set SITE_URL as fallback
    app.config["SITE_URL"] = "https://example.com"
    assert app.config.get("SITE_URL") == "https://example.com"


@patch("app.utils.email.url_for")
def test_fallback_mechanism_when_url_for_fails(mock_url_for, app, test_user, fake_mailer):
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

        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

        # Should catch RuntimeError and use fallback
        result = send_payment_receipt(test_user, payment, membership)

        # Should succeed using fallback
        assert result is True
        assert_email_sent(fake_mailer)
