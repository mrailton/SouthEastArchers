"""Password reset routes — HTTP flow and email triggers (token logic: user_service / model tests)."""

from app import db


def test_forgot_password_sends_email_for_known_user(client, test_user, app, fake_mailer):
    with app.app_context():
        import app.services.mail_service as mail_service_mod

        mail_service_mod.mail = fake_mailer
        response = client.post("/auth/forgot-password", data={"email": test_user.email}, follow_redirects=True)

    assert b"password reset link" in response.content.lower() or b"if an account exists" in response.content.lower()
    from tests.helpers import assert_email_sent

    assert_email_sent(fake_mailer, subject_contains="Reset Your Password", recipients=[test_user.email])


def test_forgot_password_same_message_for_unknown_email(client, app, fake_mailer):
    with app.app_context():
        import app.services.mail_service as mail_service_mod

        mail_service_mod.mail = fake_mailer
        response = client.post(
            "/auth/forgot-password",
            data={"email": "nonexistent@example.com"},
            follow_redirects=True,
        )

    assert b"password reset link" in response.content.lower() or b"if an account exists" in response.content.lower()
    assert len(fake_mailer.sent_messages) == 0


def test_reset_password_invalid_token_redirects(client):
    response = client.post(
        "/auth/reset-password/invalid-token",
        data={"password": "newpass123", "password_confirm": "newpass123"},
        follow_redirects=True,
    )
    assert b"Invalid or expired" in response.content


def test_reset_password_success_redirects_to_login(client, test_user):
    token = test_user.generate_reset_token()
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "NewSecurePassword123!", "password_confirm": "NewSecurePassword123!"},
        follow_redirects=True,
    )
    assert b"Password reset successfully" in response.content
    db.session.refresh(test_user)
    assert test_user.check_password("NewSecurePassword123!")
