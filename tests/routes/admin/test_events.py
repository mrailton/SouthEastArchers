"""Tests for admin event management"""

from datetime import datetime

import pytest

from app.models import Event


class TestAdminEvents:
    def test_events_list(self, client, admin_user):
        """Test viewing events list"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/events")
        assert response.status_code == 200

    def test_events_list_shows_edit_buttons(self, client, admin_user, app):
        """Test that events list shows edit buttons for each event"""
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=datetime.now(),
            published=True,
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/events")
        assert response.status_code == 200
        assert b"Test Event" in response.data
        assert f"/admin/events/{event_id}/edit".encode() in response.data
        assert b"Edit" in response.data

    def test_events_list_empty_state(self, client, admin_user):
        """Test that empty events list shows helpful message"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/events")
        assert response.status_code == 200
        assert b"No events yet" in response.data
        assert b"Create one now" in response.data

    def test_create_event_page(self, client, admin_user):
        """Test accessing create event page"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/events/create")
        assert response.status_code == 200

    def test_edit_event_page(self, client, admin_user, app):
        """Test accessing edit event page"""
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=datetime.now(),
            published=False,
        )
        db.session.add(event)
        db.session.commit()

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get(f"/admin/events/{event.id}/edit")
        assert response.status_code == 200
        assert b"Edit Event" in response.data
        assert b"Test Event" in response.data

    def test_edit_event_success(self, client, admin_user, app):
        """Test updating event"""
        from app import db

        event = Event(
            title="Original Event",
            description="Original description",
            start_date=datetime.now(),
            published=False,
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        new_date = datetime.now().strftime("%Y-%m-%dT%H:%M")
        response = client.post(
            f"/admin/events/{event_id}/edit",
            data={
                "title": "Updated Event",
                "description": "Updated description",
                "start_date": new_date,
                "location": "New Location",
                "published": "on",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify changes
        updated_event = db.session.get(Event, event_id)
        assert updated_event.title == "Updated Event"
        assert updated_event.location == "New Location"
        assert updated_event.published is True

    def test_edit_event_not_found(self, client, admin_user):
        """Test editing non-existent event"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.get("/admin/events/99999/edit")
        assert response.status_code == 404

    def test_events_requires_admin(self, client, test_user):
        """Test that events require admin"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/admin/events")
        assert response.status_code in [302, 403]

    def test_create_event_success(self, client, admin_user, app):
        """Test successfully creating an event"""
        from app import db

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        from datetime import datetime

        event_date = datetime.now().strftime("%Y-%m-%dT%H:%M")

        response = client.post(
            "/admin/events/create",
            data={
                "title": "New Event",
                "description": "Event description",
                "start_date": event_date,
                "location": "Test Location",
                "published": "on",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify event was created
        event = Event.query.filter_by(title="New Event").first()
        assert event is not None
        assert event.location == "Test Location"
        assert event.published is True

    def test_create_event_unpublished(self, client, admin_user, app):
        """Test creating an unpublished event"""
        from app import db

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        from datetime import datetime

        event_date = datetime.now().strftime("%Y-%m-%dT%H:%M")

        response = client.post(
            "/admin/events/create",
            data={
                "title": "Unpublished Event",
                "description": "Event description",
                "start_date": event_date,
                "location": "Test Location",
                # Not setting published checkbox
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verify event was created as unpublished
        event = Event.query.filter_by(title="Unpublished Event").first()
        assert event is not None
        assert event.published is False

    def test_create_event_invalid_date(self, client, admin_user):
        """Test creating event with invalid date format"""
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.post(
            "/admin/events/create",
            data={
                "title": "Bad Date Event",
                "description": "Event description",
                "start_date": "invalid-date",
                "location": "Test Location",
            },
        )

        assert response.status_code == 200
        # Pydantic error message for invalid datetime
        assert b"valid datetime" in response.data or b"Invalid" in response.data

    def test_edit_event_invalid_date(self, client, admin_user, app):
        """Test editing event with invalid date format"""
        from app import db

        event = Event(
            title="Original Event",
            description="Original description",
            start_date=datetime.now(),
            published=False,
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id

        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

        response = client.post(
            f"/admin/events/{event_id}/edit",
            data={
                "title": "Updated Event",
                "description": "Updated description",
                "start_date": "not-a-valid-date",
                "location": "New Location",
            },
        )

        assert response.status_code == 200
        # Pydantic error message for invalid datetime
        assert b"valid datetime" in response.data or b"Invalid" in response.data

    def test_create_event_requires_admin(self, client, test_user):
        """Test creating event requires admin"""
        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get("/admin/events/create")
        assert response.status_code in [302, 403]

    def test_edit_event_requires_admin(self, client, test_user, app):
        """Test editing event requires admin"""
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=datetime.now(),
            published=False,
        )
        db.session.add(event)
        db.session.commit()

        client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

        response = client.get(f"/admin/events/{event.id}/edit")
        assert response.status_code in [302, 403]
