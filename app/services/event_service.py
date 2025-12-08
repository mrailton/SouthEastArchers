from datetime import datetime

from app import db
from app.models import Event
from app.utils.datetime_utils import utc_now


class EventService:

    @staticmethod
    def create_event(
        title: str,
        start_date: datetime,
        description: str = None,
        location: str = None,
        published: bool = False,
    ) -> Event:
        """Create a new event."""
        event = Event(
            title=title,
            description=description,
            start_date=start_date,
            location=location,
            published=published,
        )

        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def update_event(
        event: Event,
        title: str,
        start_date: datetime,
        description: str = None,
        location: str = None,
        published: bool = False,
    ) -> Event:
        """Update an existing event."""
        event.title = title
        event.description = description
        event.start_date = start_date
        event.location = location
        event.published = published

        db.session.commit()
        return event

    @staticmethod
    def get_all_events() -> list[Event]:
        """Get all events ordered by start date descending."""
        return Event.query.order_by(Event.start_date.desc()).all()

    @staticmethod
    def get_upcoming_published_events() -> list[Event]:
        """Get all upcoming published events ordered by start date."""
        return Event.query.filter_by(published=True).filter(Event.start_date >= utc_now()).order_by(Event.start_date).all()

    @staticmethod
    def get_event_by_id(event_id: int) -> Event | None:
        """Get an event by ID."""
        return db.session.get(Event, event_id)

    @staticmethod
    def parse_date(date_str: str) -> datetime | None:
        """Parse ISO format date string."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
