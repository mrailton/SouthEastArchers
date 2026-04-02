from datetime import datetime

from app.models import Event
from app.repositories import EventRepository
from app.services.result import ServiceResult


class EventService:
    @staticmethod
    def create_event(
        title: str,
        start_date: datetime,
        description: str = None,
        location: str = None,
        published: bool = False,
    ) -> ServiceResult[Event]:
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
            return ServiceResult.ok(data=event)
        except Exception as e:
            return ServiceResult.fail(f"Error creating event: {str(e)}")

    @staticmethod
    def update_event(
        event: Event,
        title: str,
        start_date: datetime,
        description: str = None,
        location: str = None,
        published: bool = False,
    ) -> ServiceResult[None]:
        """Update an existing event."""
        event.title = title
        event.description = description
        event.start_date = start_date
        event.location = location
        event.published = published

        try:
            EventRepository.save()
            return ServiceResult.ok()
        except Exception as e:
            return ServiceResult.fail(f"Error updating event: {str(e)}")

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
