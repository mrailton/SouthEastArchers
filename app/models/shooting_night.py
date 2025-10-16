from datetime import datetime

from app import db


# Association table for many-to-many relationship between ShootingNight and User
shooting_attendance = db.Table('shooting_attendance',
    db.Column('shooting_night_id', db.Integer, db.ForeignKey('shooting_nights.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('credits_deducted', db.Integer, default=1),
    db.Column('recorded_at', db.DateTime, default=datetime.utcnow)
)


class ShootingNight(db.Model):
    __tablename__ = 'shooting_nights'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(50), nullable=False)  # Hall, Meadow, Woods
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref='created_shooting_nights', foreign_keys=[created_by])
    attendees = db.relationship('User', secondary=shooting_attendance, backref='attended_shooting_nights')
    
    def __repr__(self):
        return f'<ShootingNight {self.date} - {self.location}>'
