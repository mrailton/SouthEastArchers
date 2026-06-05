from datetime import datetime
from unittest.mock import patch

from app.models import Event
from app.services import events


def test_get_upcoming_published_events(app):
    from app import db

    db.session.add(
        Event(
            title="Future",
            description="Desc",
            start_date=datetime(2099, 1, 1, 12, 0),
            published=True,
        )
    )
    db.session.commit()
    upcoming = events.get_upcoming_published_events()
    assert any(e.title == "Future" for e in upcoming)


def test_create_event_failure(app):
    with patch("app.services.events.EventRepository.save", side_effect=RuntimeError("db")):
        result = events.create_event(
            title="Broken Event",
            start_date=datetime(2026, 1, 1, 10, 0),
            description="Description",
        )
    assert result.success is False


def test_update_event_success_and_failure(app):
    from app import db

    event = Event(title="Old", description="Old desc", start_date=datetime(2026, 1, 1, 10, 0))
    db.session.add(event)
    db.session.commit()

    result = events.update_event(
        event,
        title="New",
        start_date=datetime(2026, 2, 1, 10, 0),
        description="New desc",
        location="Hall",
    )
    assert result.success is True
    assert event.location == "Hall"

    with patch("app.services.events.EventRepository.save", side_effect=RuntimeError("db")):
        result = events.update_event(event, title="X", start_date=datetime(2026, 3, 1, 10, 0))
    assert result.success is False
