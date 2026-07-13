from app import db
from app.models import Event
from app.repositories import EventRepository
from app.utils.datetime_utils import utc_now


def test_event_repository_get_all(app):
    event = Event(title="Repo Event", description="Test", start_date=utc_now())
    db.session.add(event)
    db.session.commit()

    events = EventRepository.get_all()
    assert len(events) >= 1


def test_event_repository_get_by_id(app):
    event = Event(title="Find Me", description="Test", start_date=utc_now())
    db.session.add(event)
    db.session.commit()

    found = EventRepository.get_by_id(event.id)
    assert found is not None
    assert found.title == "Find Me"
