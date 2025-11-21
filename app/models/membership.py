from datetime import date, timedelta

from app import db
from app.utils.datetime_utils import utc_now


class Membership(db.Model):
    """Annual membership with included credits"""

    __tablename__ = "memberships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    credits = db.Column(db.Integer, default=20)  # Credits available (starts at 20)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def is_active(self):
        """Check if membership is currently active"""
        return self.status == "active" and self.expiry_date >= date.today()

    def credits_remaining(self):
        """Get remaining credits"""
        return max(0, self.credits)

    def use_credit(self):
        """Deduct one credit"""
        if self.credits > 0:
            self.credits -= 1
            return True
        return False

    def add_credits(self, amount):
        """Add credits (from purchase)"""
        self.credits += amount

    def renew(self):
        """Renew membership for another year"""
        self.start_date = date.today()
        self.expiry_date = date.today() + timedelta(days=365)
        self.credits = 20  # Reset to 20 credits
        self.status = "active"

    def activate(self):
        """Activate a pending membership"""
        self.status = "active"

    def __repr__(self):
        return f"<Membership user_id={self.user_id} credits={self.credits}>"
