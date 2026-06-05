from datetime import UTC

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db import Model
from app.utils.datetime_utils import utc_now


class Event(Model):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)
    location = Column(String(255))
    capacity = Column(Integer, nullable=True)
    published = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def is_upcoming(self) -> bool:
        now = utc_now()

        start = self.start_date
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return start > now

    def publish(self) -> None:
        self.published = True

    def __repr__(self) -> str:
        return f"<Event {self.title} on {self.start_date}>"
