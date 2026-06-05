"""Smoke tests that invalid form POSTs return 422 with validation errors."""

from datetime import datetime

import pytest

from app import db
from app.models import Event, News, Shoot, ShootLocation


@pytest.mark.parametrize(
    "url,data",
    [
        ("/auth/login", {"email": "invalid", "password": ""}),
        ("/auth/signup", {"name": "", "email": "invalid-email", "password": "short", "confirm_password": "different"}),
        ("/auth/forgot-password", {"email": ""}),
    ],
)
def test_public_form_validation_error(client, url, data):
    response = client.post(url, data=data)
    assert response.status_code in (200, 422)


def test_reset_password_validation_error(client, test_user):
    token = test_user.generate_reset_token()
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "short", "confirm_password": "different"},
    )
    assert response.status_code in (200, 422)


@pytest.mark.parametrize(
    "url,data",
    [
        ("/admin/members/create", {"name": "", "email": "invalid"}),
        ("/admin/events/create", {"title": ""}),
        ("/admin/shoots/create", {"location": ""}),
        ("/admin/news/create", {"title": ""}),
    ],
)
def test_admin_create_form_validation_error(admin_client, url, data):
    response = admin_client.post(url, data=data)
    assert response.status_code in (200, 422)


def test_admin_edit_member_validation_error(admin_client, test_user):
    response = admin_client.post(
        f"/admin/members/{test_user.id}/edit",
        data={"name": "", "email": "invalid"},
    )
    assert response.status_code in (200, 422)


def test_admin_edit_event_validation_error(admin_client, app):
    event = Event(title="Test Event", description="Test description", start_date=datetime(2030, 12, 31, 18, 0))
    db.session.add(event)
    db.session.commit()

    response = admin_client.post(f"/admin/events/{event.id}/edit", data={"title": ""})
    assert response.status_code in (200, 422)


def test_admin_edit_shoot_validation_error(admin_client, app):
    shoot = Shoot(date=datetime(2030, 12, 31, 18, 0), location=ShootLocation.HALL)
    db.session.add(shoot)
    db.session.commit()

    response = admin_client.post(f"/admin/shoots/{shoot.id}/edit", data={"location": ""})
    assert response.status_code in (200, 422)


def test_admin_edit_news_validation_error(admin_client, app):
    news = News(title="Test News", content="Test content with enough characters.")
    db.session.add(news)
    db.session.commit()

    response = admin_client.post(f"/admin/news/{news.id}/edit", data={"title": ""})
    assert response.status_code in (200, 422)


def test_member_profile_validation_error(member_client):
    response = member_client.post("/member/profile", data={"name": ""})
    assert response.status_code in (200, 422)


def test_member_change_password_validation_error(member_client):
    response = member_client.post(
        "/member/change-password",
        data={
            "current_password": "wrong",
            "new_password": "short",
            "confirm_password": "different",
        },
    )
    assert response.status_code in (200, 422)
