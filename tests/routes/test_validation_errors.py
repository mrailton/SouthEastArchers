"""Tests for form validation error handling across all POST routes"""


def test_login_validation_error(client):
    """Test login form validation error is displayed"""
    response = client.post("/auth/login", data={"email": "invalid", "password": ""})
    assert response.status_code == 200
    assert b"This field is required" in response.data or b"Invalid" in response.data


def test_signup_validation_error(client):
    """Test signup form validation error is displayed"""
    response = client.post(
        "/auth/signup",
        data={
            "name": "",  # Missing required field
            "email": "invalid-email",  # Invalid email
            "password": "short",
            "confirm_password": "different",  # Mismatch
        },
    )
    assert response.status_code == 200


def test_forgot_password_validation_error(client):
    """Test forgot password form validation error is displayed"""
    response = client.post("/auth/forgot-password", data={"email": ""})
    assert response.status_code == 200


def test_reset_password_validation_error(client, test_user):
    """Test reset password form validation error is displayed"""
    token = test_user.generate_reset_token()
    response = client.post(
        f"/auth/reset-password/{token}",
        data={
            "password": "short",
            "confirm_password": "different",
        },
    )
    assert response.status_code == 200


def test_admin_create_member_validation_error(client, admin_user):
    """Test admin create member form validation error"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        "/admin/members/create",
        data={
            "name": "",  # Missing required
            "email": "invalid",
        },
    )
    assert response.status_code == 200


def test_admin_edit_member_validation_error(client, admin_user, test_user):
    """Test admin edit member form validation error"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": "",  # Missing required
            "email": "invalid",
        },
    )
    assert response.status_code == 200


def test_admin_create_event_validation_error(client, admin_user):
    """Test admin create event form validation error"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        "/admin/events/create",
        data={
            "title": "",  # Missing required
        },
    )
    assert response.status_code == 200


def test_admin_edit_event_validation_error(client, admin_user, app):
    """Test admin edit event form validation error"""
    from datetime import datetime

    from app import db
    from app.models import Event

    with app.app_context():
        event = Event(title="Test Event", description="Test description", start_date=datetime(2030, 12, 31, 18, 0))
        db.session.add(event)
        db.session.commit()
        event_id = event.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        f"/admin/events/{event_id}/edit",
        data={
            "title": "",  # Missing required
        },
    )
    assert response.status_code == 200


def test_admin_create_shoot_validation_error(client, admin_user):
    """Test admin create shoot form validation error"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        "/admin/shoots/create",
        data={
            "location": "",  # Invalid
        },
    )
    assert response.status_code == 200


def test_admin_edit_shoot_validation_error(client, admin_user, app):
    """Test admin edit shoot form validation error"""
    from datetime import datetime

    from app import db
    from app.models import Shoot, ShootLocation

    with app.app_context():
        shoot = Shoot(date=datetime(2030, 12, 31, 18, 0), location=ShootLocation.HALL)
        db.session.add(shoot)
        db.session.commit()
        shoot_id = shoot.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        f"/admin/shoots/{shoot_id}/edit",
        data={
            "location": "",  # Invalid
        },
    )
    assert response.status_code == 200


def test_admin_create_news_validation_error(client, admin_user):
    """Test admin create news form validation error"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        "/admin/news/create",
        data={
            "title": "",  # Missing required
        },
    )
    assert response.status_code == 200


def test_admin_edit_news_validation_error(client, admin_user, app):
    """Test admin edit news form validation error"""
    from app import db
    from app.models import News

    with app.app_context():
        news = News(title="Test News", content="Test content")
        db.session.add(news)
        db.session.commit()
        news_id = news.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    response = client.post(
        f"/admin/news/{news_id}/edit",
        data={
            "title": "",  # Missing required
        },
    )
    assert response.status_code == 200


def test_member_profile_validation_error(client, test_user):
    """Test member profile form validation error"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})
    response = client.post(
        "/member/profile",
        data={
            "name": "",  # Missing required
        },
    )
    assert response.status_code == 200


def test_member_change_password_validation_error(client, test_user):
    """Test member change password form validation error"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})
    response = client.post(
        "/member/change-password",
        data={
            "current_password": "wrong",
            "new_password": "short",
            "confirm_password": "different",
        },
    )
    assert response.status_code == 200
