from datetime import datetime
from app.utils.datetime_utils import utc_now
from app import db


class Credit(db.Model):
    """Additional credits for extra shooting nights beyond annual membership"""
    __tablename__ = 'credits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Integer, default=1)  # Number of credits purchased
    purchase_date = db.Column(db.DateTime, default=utc_now)
    expiry_date = db.Column(db.DateTime, nullable=True)  # Credits may expire
    used = db.Column(db.Integer, default=0)  # Number of credits used
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def balance(self):
        """Get remaining credit balance"""
        return max(0, self.amount - self.used)
    
    def is_expired(self):
        """Check if credits have expired"""
        if not self.expiry_date:
            return False
        return utc_now() > self.expiry_date
    
    def __repr__(self):
        return f'<Credit user_id={self.user_id} balance={self.balance()}>'
