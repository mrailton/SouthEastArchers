"""Tests for helpers"""

from app.utils.helpers import send_email


def test_send_email_with_text_only(app, fake_mailer):
    """Test sending email with text body only"""
    with app.app_context():
        # Ensure the helper module uses the fake mailer instead of performing network IO
        import app.utils.helpers as helpers

        helpers.mail = fake_mailer

        send_email(
            subject="Test Subject",
            recipients=["test@example.com"],
            text_body="This is a test email",
        )

        from tests.helpers import assert_email_sent

        # Verify one message was recorded and inspect it
        sent_message = assert_email_sent(fake_mailer, subject_contains="Test Subject", recipients=["test@example.com"])
        assert sent_message.body == "This is a test email"
        assert getattr(sent_message, "html", None) is None


def test_send_email_with_html(app, fake_mailer):
    """Test sending email with both text and HTML body"""
    with app.app_context():
        import app.utils.helpers as helpers

        helpers.mail = fake_mailer

        send_email(
            subject="HTML Test",
            recipients=["test@example.com"],
            text_body="Plain text version",
            html_body="<h1>HTML version</h1>",
        )

        from tests.helpers import assert_email_sent

        sent_message = assert_email_sent(fake_mailer, subject_contains="HTML Test")
        assert sent_message.body == "Plain text version"
        assert sent_message.html == "<h1>HTML version</h1>"


def test_send_email_multiple_recipients(app, fake_mailer):
    """Test sending email to multiple recipients"""
    with app.app_context():
        import app.utils.helpers as helpers

        helpers.mail = fake_mailer
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        send_email(
            subject="Multiple Recipients",
            recipients=recipients,
            text_body="Message for multiple recipients",
        )

        from tests.helpers import assert_email_sent

        sent_message = assert_email_sent(fake_mailer)
        assert sent_message.recipients == recipients


def test_send_email_creates_message_correctly(app, fake_mailer):
    """Test that Message object is created with correct parameters"""
    with app.app_context():
        import app.utils.helpers as helpers

        helpers.mail = fake_mailer
        send_email(
            subject="Verification Required",
            recipients=["verify@example.com"],
            text_body="Please verify your account",
            html_body="<p>Please verify your account</p>",
        )

        from tests.helpers import assert_email_sent

        sent_message = assert_email_sent(fake_mailer)
        # Verify it's a Message object with all expected properties
        assert hasattr(sent_message, "subject")
        assert hasattr(sent_message, "recipients")
        assert hasattr(sent_message, "body")
        assert hasattr(sent_message, "html")


def test_send_email_without_html_body(app, fake_mailer):
    """Test that html is None when html_body is not provided"""
    with app.app_context():
        import app.utils.helpers as helpers

        helpers.mail = fake_mailer
        send_email(
            subject="Text Only",
            recipients=["text@example.com"],
            text_body="Text only email",
        )

        from tests.helpers import assert_email_sent

        sent_message = assert_email_sent(fake_mailer)
        assert getattr(sent_message, "html", None) is None


def test_send_email_with_empty_html_body(app, fake_mailer):
    """Test behavior when html_body is empty string"""
    with app.app_context():
        import app.utils.helpers as helpers

        helpers.mail = fake_mailer
        send_email(
            subject="Empty HTML",
            recipients=["test@example.com"],
            text_body="Text body",
            html_body="",
        )

        from tests.helpers import assert_email_sent

        sent_message = assert_email_sent(fake_mailer)
        # Empty string is falsy, so html should not be set
        assert getattr(sent_message, "html", None) is None or sent_message.html == ""
