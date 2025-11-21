from datetime import datetime, timezone
from app.utils.datetime_utils import utc_now
from app import db


class Event(db.Model):
    """Club events"""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    capacity = db.Column(db.Integer, nullable=True)
    published = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def is_upcoming(self):
        """Check if event is in the future"""
        now = utc_now()
        # Handle timezone-naive datetimes from database
        start = self.start_date
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return start > now

    def publish(self):
        """Publish the event"""
        self.published = True

    def __repr__(self):
        return f"<Event {self.title} on {self.start_date}>"
