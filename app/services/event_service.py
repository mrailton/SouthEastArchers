from datetime import datetime

from app.models import Event
from app.repositories import EventRepository


class EventService:
    @staticmethod
    def create_event(
        title: str,
        start_date: datetime,
        description: str = None,
        location: str = None,
        published: bool = False,
    ) -> tuple[Event | None, str | None]:
        """Create a new event."""
        event = Event(
            title=title,
            description=description,
            start_date=start_date,
            location=location,
            published=published,
        )

        try:
            EventRepository.add(event)
            EventRepository.save()
            return event, None
        except Exception as e:
            return None, f"Error creating event: {str(e)}"

    @staticmethod
    def update_event(
        event: Event,
        title: str,
        start_date: datetime,
        description: str = None,
        location: str = None,
        published: bool = False,
    ) -> tuple[bool, str | None]:
        """Update an existing event."""
        event.title = title
        event.description = description
        event.start_date = start_date
        event.location = location
        event.published = published

        try:
            EventRepository.save()
            return True, None
        except Exception as e:
            return False, f"Error updating event: {str(e)}"

    @staticmethod
    def get_all_events() -> list[Event]:
        """Get all events ordered by start date descending."""
        return EventRepository.get_all()

    @staticmethod
    def get_upcoming_published_events() -> list[Event]:
        """Get all upcoming published events ordered by start date."""
        return EventRepository.get_upcoming_published()

    @staticmethod
    def get_event_by_id(event_id: int) -> Event | None:
        """Get an event by ID."""
        return EventRepository.get_by_id(event_id)

    @staticmethod
    def parse_date(date_str: str) -> datetime | None:
        """Parse ISO format date string."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
