from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
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
        from app.models.membership import Membership
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
