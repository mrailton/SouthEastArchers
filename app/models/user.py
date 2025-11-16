from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.utils.datetime_utils import utc_now


class User(db.Model):
    """User model for members and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationships
    membership = db.relationship('Membership', backref='user', uselist=False, cascade='all, delete-orphan')
    credits = db.relationship('Credit', backref='user', cascade='all, delete-orphan')
    shooting_nights = db.relationship('ShootingNight', secondary='user_shooting_nights', backref='users')
    payments = db.relationship('Payment', backref='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_age(self):
        """Calculate age from date of birth"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def __repr__(self):
        return f'<User {self.email}>'
