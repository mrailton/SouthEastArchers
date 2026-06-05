"""Password reset routes — HTTP flow and email triggers (token logic: users / model tests)."""

from app import db


def test_forgot_password_sends_email_for_known_user(client, test_user, mocker):
    mock_send = mocker.patch("app.services.mail.send_password_reset")
    response = client.post("/auth/forgot-password", data={"email": test_user.email}, follow_redirects=True)

    assert b"password reset link" in response.content.lower() or b"if an account exists" in response.content.lower()
    mock_send.assert_called_once()
    assert mock_send.call_args[0][0] == test_user.id


def test_forgot_password_same_message_for_unknown_email(client):
    response = client.post(
        "/auth/forgot-password",
        data={"email": "nonexistent@example.com"},
        follow_redirects=True,
    )

    assert b"password reset link" in response.content.lower() or b"if an account exists" in response.content.lower()


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
