"""Repository for Event model data access."""

from __future__ import annotations

from app import db
from app.models import Event
from app.repositories.base import BaseRepository
from app.utils.datetime_utils import utc_now


class EventRepository(BaseRepository):
    @staticmethod
    def get_by_id(event_id: int) -> Event | None:
        return db.session.get(Event, event_id)

    @staticmethod
    def get_all() -> list[Event]:
        return Event.query.order_by(Event.start_date.desc()).all()

    @staticmethod
    def get_upcoming_published() -> list[Event]:
        return Event.query.filter_by(published=True).filter(Event.start_date >= utc_now()).order_by(Event.start_date).all()

    @staticmethod
    def add(event: Event) -> None:
        db.session.add(event)
