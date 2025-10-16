from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = db.relationship('Membership', backref='user', lazy=True, cascade='all, delete-orphan')
    credit_purchases = db.relationship('CreditPurchase', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def current_membership(self):
        """Get the current active membership"""
        return Membership.query.filter_by(
            user_id=self.id,
            is_active=True
        ).filter(
            Membership.end_date >= datetime.utcnow()
        ).first()
    
    @property
    def total_credits(self):
        """Calculate total available credits"""
        credits = 0
        membership = self.current_membership
        if membership:
            credits += membership.credits_remaining
        return credits
    
    def __repr__(self):
        return f'<User {self.email}>'


class Membership(db.Model):
    __tablename__ = 'memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    credits_remaining = db.Column(db.Integer, default=20)
    is_active = db.Column(db.Boolean, default=True)
    amount_paid = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Membership {self.user_id} - {self.start_date} to {self.end_date}>'


class CreditPurchase(db.Model):
    __tablename__ = 'credit_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credits_purchased = db.Column(db.Integer, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CreditPurchase {self.user_id} - {self.credits_purchased} credits>'


class News(db.Model):
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship('User', backref='news_posts')
    
    def __repr__(self):
        return f'<News {self.title}>'


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    published = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref='events')
    
    def __repr__(self):
        return f'<Event {self.title}>'


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
