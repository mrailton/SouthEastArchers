from unittest.mock import MagicMock, patch

from app.utils.mail import send_email


def test_send_email_ssl_with_login():
    mock_settings = MagicMock(
        mail_default_sender="noreply@example.com",
        mail_server="smtp.example.com",
        mail_port=465,
        mail_use_ssl=True,
        mail_use_tls=False,
        mail_username="user",
        mail_password="pass",
    )
    mock_smtp = MagicMock()
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_smtp
    with (
        patch("app.utils.mail.get_settings", return_value=mock_settings),
        patch("app.utils.mail.smtplib.SMTP_SSL", return_value=mock_context),
    ):
        send_email("Subject", ["a@example.com"], "Body", "<p>Body</p>")
    mock_smtp.login.assert_called_once()


def test_send_email_tls_without_ssl():
    mock_settings = MagicMock(
        mail_default_sender="noreply@example.com",
        mail_server="smtp.example.com",
        mail_port=587,
        mail_use_ssl=False,
        mail_use_tls=True,
        mail_username="",
        mail_password="",
    )
    mock_smtp = MagicMock()
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_smtp
    with (
        patch("app.utils.mail.get_settings", return_value=mock_settings),
        patch("app.utils.mail.smtplib.SMTP", return_value=mock_context),
    ):
        send_email("Subject", ["a@example.com"], "Body")
    mock_smtp.starttls.assert_called_once()


def test_send_email_logs_failure():
    mock_settings = MagicMock(
        mail_default_sender="noreply@example.com",
        mail_server="smtp.example.com",
        mail_port=587,
        mail_use_ssl=False,
        mail_use_tls=False,
        mail_username="",
        mail_password="",
    )
    with (
        patch("app.utils.mail.get_settings", return_value=mock_settings),
        patch("app.utils.mail.smtplib.SMTP", side_effect=OSError("network")),
        patch("app.utils.mail.logger.exception") as mock_log,
    ):
        send_email("Subject", ["a@example.com"], "Body")
    mock_log.assert_called_once()
