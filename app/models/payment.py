from datetime import datetime
from app.utils.datetime_utils import utc_now
from app import db


class Payment(db.Model):
    """Payment transactions"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='EUR')
    payment_type = db.Column(db.Enum('membership', 'credits'), nullable=False)
    payment_method = db.Column(db.Enum('cash', 'online'), nullable=False, default='online')
    status = db.Column(db.Enum('pending', 'completed', 'failed', 'cancelled'), default='pending', index=True)
    sumup_transaction_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    sumup_receipt_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def mark_completed(self, sumup_transaction_id=None, receipt_url=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.sumup_transaction_id = sumup_transaction_id
        self.sumup_receipt_url = receipt_url
    
    def mark_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
    
    def __repr__(self):
        return f'<Payment {self.id} user_id={self.user_id} {self.status}>'
