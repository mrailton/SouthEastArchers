from datetime import datetime

from app import db


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
