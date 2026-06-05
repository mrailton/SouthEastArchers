"""Admin event routes — permissions and form handling."""

from datetime import datetime

from app.models import Event


def test_events_list(admin_client):
    response = admin_client.get("/admin/events")
    assert response.status_code == 200


def test_create_event_success_redirects(admin_client):
    event_date = datetime.now().strftime("%Y-%m-%dT%H:%M")
    response = admin_client.post(
        "/admin/events/create",
        data={
            "title": "New Event",
            "description": "Event description",
            "start_date": event_date,
            "location": "Test Location",
            "published": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert Event.query.filter_by(title="New Event").first() is not None


def test_create_event_invalid_date_returns_422(admin_client):
    response = admin_client.post(
        "/admin/events/create",
        data={
            "title": "Bad Date Event",
            "description": "Event description",
            "start_date": "invalid-date",
            "location": "Test Location",
        },
    )
    assert response.status_code == 422


def test_edit_event_not_found(admin_client):
    response = admin_client.get("/admin/events/99999/edit")
    assert response.status_code == 404


def test_events_requires_admin(member_client):
    response = member_client.get("/admin/events")
    assert response.status_code in (302, 403)
