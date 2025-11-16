from datetime import datetime
from app.utils.datetime_utils import utc_now
from app import db

# Association table for many-to-many relationship
user_shooting_nights = db.Table(
    'user_shooting_nights',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('shooting_night_id', db.Integer, db.ForeignKey('shooting_nights.id'), primary_key=True),
    db.Column('credits_used', db.Integer, default=1),
    db.Column('attended_at', db.DateTime)
)


class ShootingNight(db.Model):
    """Shooting night sessions available to members"""
    __tablename__ = 'shooting_nights'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def is_full(self):
        """Check if shooting night is at capacity"""
        return len(self.users) >= self.capacity
    
    def spots_remaining(self):
        """Get number of remaining spots"""
        return max(0, self.capacity - len(self.users))
    
    def __repr__(self):
        return f'<ShootingNight {self.date} at {self.location}>'
