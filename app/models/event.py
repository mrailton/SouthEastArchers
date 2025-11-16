from datetime import datetime
from app.utils.datetime_utils import utc_now
from app import db


class Event(db.Model):
    """Club events"""
    __tablename__ = 'events'
    
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
        return self.start_date > utc_now()
    
    def publish(self):
        """Publish the event"""
        self.published = True
    
    def __repr__(self):
        return f'<Event {self.title} on {self.start_date}>'
