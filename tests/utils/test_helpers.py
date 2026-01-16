"""Tests for helpers"""

from unittest.mock import patch

from app.utils.helpers import send_email


@patch("app.utils.helpers.mail.send")
def test_send_email_with_text_only(mock_send, app):
    """Test sending email with text body only"""
    with app.app_context():
        send_email(
            subject="Test Subject",
            recipients=["test@example.com"],
            text_body="This is a test email",
        )

        # Verify mail.send was called once
        assert mock_send.call_count == 1

        # Get the message that was sent
        sent_message = mock_send.call_args[0][0]
        assert sent_message.subject == "Test Subject"
        assert sent_message.recipients == ["test@example.com"]
        assert sent_message.body == "This is a test email"
        assert sent_message.html is None


@patch("app.utils.helpers.mail.send")
def test_send_email_with_html(mock_send, app):
    """Test sending email with both text and HTML body"""
    with app.app_context():
        send_email(
            subject="HTML Test",
            recipients=["test@example.com"],
            text_body="Plain text version",
            html_body="<h1>HTML version</h1>",
        )

        assert mock_send.call_count == 1
        sent_message = mock_send.call_args[0][0]
        assert sent_message.subject == "HTML Test"
        assert sent_message.body == "Plain text version"
        assert sent_message.html == "<h1>HTML version</h1>"


@patch("app.utils.helpers.mail.send")
def test_send_email_multiple_recipients(mock_send, app):
    """Test sending email to multiple recipients"""
    with app.app_context():
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        send_email(
            subject="Multiple Recipients",
            recipients=recipients,
            text_body="Message for multiple recipients",
        )

        assert mock_send.call_count == 1
        sent_message = mock_send.call_args[0][0]
        assert sent_message.recipients == recipients


@patch("app.utils.helpers.mail.send")
def test_send_email_creates_message_correctly(mock_send, app):
    """Test that Message object is created with correct parameters"""
    with app.app_context():
        send_email(
            subject="Verification Required",
            recipients=["verify@example.com"],
            text_body="Please verify your account",
            html_body="<p>Please verify your account</p>",
        )

        sent_message = mock_send.call_args[0][0]
        # Verify it's a Message object with all expected properties
        assert hasattr(sent_message, "subject")
        assert hasattr(sent_message, "recipients")
        assert hasattr(sent_message, "body")
        assert hasattr(sent_message, "html")


@patch("app.utils.helpers.mail.send")
def test_send_email_without_html_body(mock_send, app):
    """Test that html is None when html_body is not provided"""
    with app.app_context():
        send_email(
            subject="Text Only",
            recipients=["text@example.com"],
            text_body="Text only email",
        )

        sent_message = mock_send.call_args[0][0]
        assert sent_message.html is None


@patch("app.utils.helpers.mail.send")
def test_send_email_with_empty_html_body(mock_send, app):
    """Test behavior when html_body is empty string"""
    with app.app_context():
        send_email(
            subject="Empty HTML",
            recipients=["test@example.com"],
            text_body="Text body",
            html_body="",
        )

        sent_message = mock_send.call_args[0][0]
        # Empty string is falsy, so html should not be set
        assert sent_message.html is None or sent_message.html == ""
