from __future__ import annotations

from datetime import datetime

from app.models.event import Event
from app.repositories import EventRepository
from app.services.result import ServiceResult


def get_upcoming_published_events() -> list[Event]:
    return EventRepository.get_upcoming_published()


def create_event(
    title: str,
    start_date: datetime,
    description: str | None = None,
    location: str | None = None,
    published: bool = False,
) -> ServiceResult[Event]:
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
    except Exception as exc:
        return ServiceResult.fail(f"Error creating event: {exc}")


def update_event(
    event: Event,
    title: str,
    start_date: datetime,
    description: str | None = None,
    location: str | None = None,
    published: bool = False,
) -> ServiceResult[None]:
    event.title = title
    event.description = description
    event.start_date = start_date
    event.location = location
    event.published = published

    try:
        EventRepository.save()
        return ServiceResult.ok()
    except Exception as exc:
        return ServiceResult.fail(f"Error updating event: {exc}")


def get_all_events() -> list[Event]:
    return EventRepository.get_all()


def get_event_by_id(event_id: int) -> Event | None:
    return EventRepository.get_by_id(event_id)
