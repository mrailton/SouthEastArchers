from app.models import User


def test_login_invalid_password(client, test_user):
    """Test login with invalid password"""
    response = client.post("/auth/login", data={"email": test_user.email, "password": "wrongpassword"})
    assert response.status_code in (200, 422)
    assert b"Invalid" in response.content


def test_login_nonexistent_user(client):
    """Test login with nonexistent email"""
    response = client.post(
        "/auth/login",
        data={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code in (200, 422)
    assert b"Invalid" in response.content


def test_signup_new_user(client):
    response = client.post(
        "/auth/signup",
        data={
            "name": "New User",
            "email": "newuser@example.com",
            "phone": "1234567890",
            "password": "password123",
            "password_confirm": "password123",
            "qualification": "Beginner Certificate",
        },
        follow_redirects=True,
    )

    assert response.status_code in (200, 422)
    assert b"Thank you for signing up. A coach will review your information shortly and get back to you to discuss membership." in response.content


def test_logout(client, test_user):
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("location") == "/"


def test_login_inactive_user(client, app):
    from app import db

    user = User(
        name="Inactive User",
        email="inactive@example.com",
        is_active=False,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/auth/login",
        data={"email": "inactive@example.com", "password": "password123"},
    )
    assert response.status_code == 422
    assert b"not currently active" in response.content


def test_login_with_next_parameter(client, test_user):
    """Test login redirects to next parameter"""
    response = client.post(
        "/auth/login?next=/member/profile",
        data={"email": test_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/member/profile" in response.headers.get("location", "")


def test_signup_password_mismatch(client):
    """Test signup with mismatched passwords"""
    response = client.post(
        "/auth/signup",
        data={
            "name": "New User",
            "email": "newuser@example.com",
            "phone": "1234567890",
            "password": "password123",
            "password_confirm": "differentpassword",
            "payment_method": "cash",
        },
    )
    assert response.status_code in (200, 422)
    assert "do not match" in response.text.lower()


def test_forgot_password_email_send_failure(client, test_user, mocker):
    """Test forgot password when email sending fails"""
    # Mock password_reset_requested signal to raise an exception
    mock_send = mocker.patch("app.events.password_reset_requested.send", side_effect=Exception("SMTP Error"))

    response = client.post(
        "/auth/forgot-password",
        data={"email": test_user.email},
        follow_redirects=True,
    )

    assert response.status_code in (200, 422)
    assert b"error occurred sending the email" in response.content
    mock_send.assert_called_once()


def test_signup_sends_new_member_notification(client, mocker):
    """A successful signup triggers user_registered event with the new user's id."""
    mock_signal = mocker.patch("app.events.user_registered.send")

    response = client.post(
        "/auth/signup",
        data={
            "name": "Notify User",
            "email": "notify_user@example.com",
            "phone": "0871234567",
            "password": "password123",
            "password_confirm": "password123",
            "qualification": "Beginner Certificate",
        },
        follow_redirects=True,
    )

    assert response.status_code in (200, 422)
    assert mock_signal.called
    # The signal should be sent with user_id as a keyword arg
    called_kwargs = mock_signal.call_args[1]
    assert isinstance(called_kwargs["user_id"], int)
