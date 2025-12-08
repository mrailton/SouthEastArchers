from datetime import datetime

from app import db
from app.utils.datetime_utils import utc_now


class Payment(db.Model):
    """Payment transactions"""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    amount_cents = db.Column(db.Integer, nullable=False)  # Store amount in cents
    currency = db.Column(db.String(3), default="EUR")
    payment_type = db.Column(db.Enum("membership", "credits"), nullable=False)
    payment_method = db.Column(
        db.Enum("cash", "online"), nullable=False, default="online"
    )
    status = db.Column(
        db.Enum("pending", "completed", "failed", "cancelled"),
        default="pending",
        index=True,
    )
    description = db.Column(db.Text)
    payment_processor = db.Column(
        db.String(50), nullable=True
    )  # e.g., 'sumup', 'stripe', etc.
    external_transaction_id = db.Column(
        db.String(255), unique=True, nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def mark_completed(self, transaction_id=None, processor=None):
        """Mark payment as completed"""
        self.status = "completed"
        self.external_transaction_id = transaction_id
        self.payment_processor = processor

    def mark_failed(self):
        """Mark payment as failed"""
        self.status = "failed"

    @property
    def amount(self):
        """Get amount in euros (for display)"""
        return self.amount_cents / 100.0

    @amount.setter
    def amount(self, value):
        """Set amount from euros (converts to cents)"""
        self.amount_cents = int(round(value * 100))

    def __repr__(self):
        return f"<Payment {self.id} user_id={self.user_id} {self.status}>"
