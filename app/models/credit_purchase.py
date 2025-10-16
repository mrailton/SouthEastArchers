from datetime import datetime

from app import db


class CreditPurchase(db.Model):
    __tablename__ = 'credit_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credits_purchased = db.Column(db.Integer, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CreditPurchase {self.user_id} - {self.credits_purchased} credits>'
