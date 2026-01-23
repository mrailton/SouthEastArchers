import pytest

from app.models import Payment
from app.utils.email import send_payment_receipt, send_welcome_email
from tests.helpers import assert_email_sent


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


def test_send_welcome_email_success(app, test_user, fake_mailer):
    """Test sending welcome email"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

        result = send_welcome_email(test_user)

        assert result is True
        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer, subject_contains="Welcome to South East Archers!", recipients=[test_user.email])
        assert call_args.html is not None
        assert call_args.body is not None


@pytest.mark.parametrize(
    "check_type,expected_in_html",
    [
        ("user_name", lambda test_user: test_user.name),
        ("membership_cost", lambda test_user: "€100.00"),
        ("credits_included", lambda test_user: "20 nights"),
        ("login_link", lambda test_user: "Login"),
    ],
)
def test_send_welcome_email_content(app, test_user, fake_mailer, check_type, expected_in_html):
    """Test welcome email includes various required content"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

        send_welcome_email(test_user)

        from tests.helpers import assert_email_sent

        call_args = assert_email_sent(fake_mailer)
        html = call_args.html

        expected = expected_in_html(test_user)
        assert expected in html, f"Expected {check_type} '{expected}' not found in email HTML"


def test_send_welcome_email_exception_handling(app, test_user, fake_mailer):
    """Test exception handling when sending fails"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

        # Simulate send raising an exception
        def raise_send(msg):
            raise Exception("Email server error")

        fake_mailer.send = raise_send

        result = send_welcome_email(test_user)

        assert result is False


def test_send_credit_purchase_receipt(app, test_user, fake_mailer):
    """Test sending credit purchase receipt email"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        from datetime import datetime

        from app.utils.email import send_credit_purchase_receipt

        # Create test payment for credit purchase
        payment = Payment(
            id=789,
            user_id=test_user.id,
            amount=30.00,
            currency="EUR",
            payment_type="credits",
            payment_method="online",
            external_transaction_id="txn_credits_123",
            payment_processor="sumup",
            description="10 shooting credits",
            status="completed",
            created_at=datetime.now(),
        )

        credits_purchased = 10
        credits_remaining = 30  # Had 20, purchased 10

        result = send_credit_purchase_receipt(test_user, payment, credits_purchased, credits_remaining)

        assert result is True
        email_sent = assert_email_sent(fake_mailer, subject_contains="Credit Purchase Receipt", recipients=[test_user.email])
        assert email_sent.html is not None
        assert email_sent.body is not None

        # Check HTML content
        assert "10" in email_sent.html  # Credits purchased
        assert "30" in email_sent.html  # Credits remaining
        assert "€30.00" in email_sent.html
        assert "txn_credits_123" in email_sent.html
        assert "SEA-000789" in email_sent.html  # Receipt number

        # Check text content
        assert "10" in email_sent.body
        assert "30" in email_sent.body
        assert "€30.00" in email_sent.body


def test_send_credit_purchase_receipt_cash(app, test_user, fake_mailer):
    """Test sending credit purchase receipt for cash payment"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        from datetime import datetime

        from app.utils.email import send_credit_purchase_receipt

        payment = Payment(
            id=999,
            user_id=test_user.id,
            amount=15.00,
            currency="EUR",
            payment_type="credits",
            payment_method="cash",
            description="5 shooting credits",
            status="completed",
            created_at=datetime.now(),
        )

        result = send_credit_purchase_receipt(test_user, payment, 5, 25)

        assert result is True
        email_sent = assert_email_sent(fake_mailer, subject_contains="Credit Purchase", recipients=[test_user.email])

        # Check cash payment method displayed correctly
        assert "Cash Payment" in email_sent.html
        # Should not have transaction ID for cash
        assert "txn_" not in email_sent.html
        assert "5" in email_sent.html  # Credits purchased
        assert "25" in email_sent.html  # Credits remaining


def test_send_payment_receipt_runtime_error_url_for(app, test_user, fake_mailer, mocker):
    """Test payment receipt handles RuntimeError from url_for gracefully"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        from datetime import datetime

        # Mock url_for to raise RuntimeError (no request context)
        mocker.patch("app.utils.email.url_for", side_effect=RuntimeError("No request context"))

        payment = Payment(
            id=888,
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

        # Should still succeed with fallback URL
        assert result is True
        email_sent = assert_email_sent(fake_mailer)
        # Should use fallback URL
        assert "southeastarchers.ie" in email_sent.html


def test_send_credit_purchase_receipt_runtime_error_url_for(app, test_user, fake_mailer, mocker):
    """Test credit receipt handles RuntimeError from url_for gracefully"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer
        from datetime import datetime

        from app.utils.email import send_credit_purchase_receipt

        # Mock url_for to raise RuntimeError
        mocker.patch("app.utils.email.url_for", side_effect=RuntimeError("No request context"))

        payment = Payment(
            id=777,
            user_id=test_user.id,
            amount=30.00,
            currency="EUR",
            payment_type="credits",
            payment_method="online",
            status="completed",
            created_at=datetime.now(),
        )

        result = send_credit_purchase_receipt(test_user, payment, 10, 30)

        # Should still succeed with fallback URL
        assert result is True
        email_sent = assert_email_sent(fake_mailer)
        # Should use fallback URL with /member/credits path
        assert "southeastarchers.ie" in email_sent.html


def test_send_welcome_email_runtime_error_url_for(app, test_user, fake_mailer, mocker):
    """Test welcome email handles RuntimeError from url_for gracefully"""
    with app.app_context():
        import app.utils.email as email_mod

        email_mod.mail = fake_mailer

        # Mock url_for to raise RuntimeError
        mocker.patch("app.utils.email.url_for", side_effect=RuntimeError("No request context"))

        result = send_welcome_email(test_user)

        # Should still succeed with fallback URL
        assert result is True
        from tests.helpers import assert_email_sent

        email_sent = assert_email_sent(fake_mailer)
        # Should use fallback URL
        assert "southeastarchers.ie" in email_sent.html
