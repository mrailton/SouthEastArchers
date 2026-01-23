from app.models import User


def test_login_page_get(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_signup_page_get(client):
    response = client.get("/auth/signup")
    assert response.status_code == 200
    assert b"Sign Up" in response.data


def test_login_valid_credentials(client, test_user):
    """Test login with valid credentials"""
    response = client.post(
        "/auth/login",
        data={"email": test_user.email, "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_login_invalid_password(client, test_user):
    """Test login with invalid password"""
    response = client.post("/auth/login", data={"email": test_user.email, "password": "wrongpassword"})
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_login_nonexistent_user(client):
    """Test login with nonexistent email"""
    response = client.post(
        "/auth/login",
        data={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


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

    assert response.status_code == 200
    assert b"Thank you for signing up. A coach will review your information shortly and get back to you to discuss membership." in response.data


def test_signup_existing_email(client, test_user):
    """Test signup with existing email"""
    response = client.post(
        "/auth/signup",
        data={
            "name": "Another User",
            "email": test_user.email,
            "phone": "1234567890",
            "password": "password123",
            "password_confirm": "password123",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 200


def test_logout(client, test_user):
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200


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
    assert response.status_code == 200


def test_login_with_next_parameter(client, test_user):
    """Test login redirects to next parameter"""
    response = client.post(
        "/auth/login?next=/member/profile",
        data={"email": test_user.email, "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/member/profile" in response.location


def test_login_remember_me(client, test_user):
    """Test login with remember me checkbox"""
    response = client.post(
        "/auth/login",
        data={
            "email": test_user.email,
            "password": "password123",
            "remember": True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


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
    assert response.status_code == 200
    assert b"do not match" in response.data


def test_forgot_password_email_send_failure(client, test_user, mocker):
    """Test forgot password when email sending fails"""
    # Mock send_password_reset_email to raise an exception
    mock_send = mocker.patch("app.routes.auth.send_password_reset_email", side_effect=Exception("SMTP Error"))

    response = client.post(
        "/auth/forgot-password",
        data={"email": test_user.email},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"error occurred sending the email" in response.data
    mock_send.assert_called_once()


def test_forgot_password_form_validation_error(client):
    """Test forgot password with invalid form data"""
    response = client.post(
        "/auth/forgot-password",
        data={"email": "not-an-email"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Form should be re-displayed with errors
