import app.utils.mail as mail_mod


def test_send_email_with_text_only(fake_mailer):
    mail_mod.send_email(
        subject="Test Subject",
        recipients=["test@example.com"],
        text_body="This is a test email",
    )

    from tests.helpers import assert_email_sent

    sent_message = assert_email_sent(fake_mailer, subject_contains="Test Subject", recipients=["test@example.com"])
    assert sent_message.body == "This is a test email"
    assert sent_message.html is None


def test_send_email_with_html(fake_mailer):
    mail_mod.send_email(
        subject="HTML Test",
        recipients=["test@example.com"],
        text_body="Plain text version",
        html_body="<h1>HTML version</h1>",
    )

    from tests.helpers import assert_email_sent

    sent_message = assert_email_sent(fake_mailer, subject_contains="HTML Test")
    assert sent_message.body == "Plain text version"
    assert sent_message.html == "<h1>HTML version</h1>"


def test_send_email_multiple_recipients(fake_mailer):
    recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
    mail_mod.send_email(
        subject="Multiple Recipients",
        recipients=recipients,
        text_body="Message for multiple recipients",
    )

    from tests.helpers import assert_email_sent

    sent_message = assert_email_sent(fake_mailer)
    assert sent_message.recipients == recipients


def test_send_email_creates_message_correctly(fake_mailer):
    mail_mod.send_email(
        subject="Verification Required",
        recipients=["verify@example.com"],
        text_body="Please verify your account",
        html_body="<p>Please verify your account</p>",
    )

    from tests.helpers import assert_email_sent

    sent_message = assert_email_sent(fake_mailer, subject_contains="Verification Required", recipients=["verify@example.com"])
    assert sent_message.body == "Please verify your account"
    assert sent_message.html == "<p>Please verify your account</p>"


def test_send_email_without_html_body(fake_mailer):
    mail_mod.send_email(
        subject="Text Only",
        recipients=["text@example.com"],
        text_body="No HTML here",
    )

    from tests.helpers import assert_email_sent

    sent_message = assert_email_sent(fake_mailer)
    assert sent_message.html is None


def test_send_email_with_empty_html_body(fake_mailer):
    mail_mod.send_email(
        subject="Empty HTML",
        recipients=["empty@example.com"],
        text_body="Text content",
        html_body="",
    )

    from tests.helpers import assert_email_sent

    sent_message = assert_email_sent(fake_mailer)
    assert sent_message.body == "Text content"
