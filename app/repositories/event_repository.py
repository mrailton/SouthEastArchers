"""Repository for Event model data access."""

from __future__ import annotations

from sqlalchemy import func, select

from app.db import db
from app.models import Event
from app.repositories.base import BaseRepository
from app.utils.datetime_utils import utc_now


class EventRepository(BaseRepository):
    @staticmethod
    def get_by_id(event_id: int) -> Event | None:
        return db.session.get(Event, event_id)

    @staticmethod
    def get_all() -> list[Event]:
        stmt = select(Event).order_by(Event.start_date.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_upcoming_published() -> list[Event]:
        stmt = select(Event).where(Event.published.is_(True), Event.start_date >= utc_now()).order_by(Event.start_date)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(event: Event) -> None:
        db.session.add(event)

    @staticmethod
    def count_upcoming() -> int:
        stmt = select(func.count()).select_from(Event).where(Event.start_date > utc_now())
        return db.session.scalar(stmt) or 0
