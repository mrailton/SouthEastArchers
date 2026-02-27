"""Financial transaction model for tracking club income and expenses."""

from app import db
from app.utils.datetime_utils import utc_now

EXPENSE_CATEGORIES = [
    ("equipment", "Equipment"),
    ("venue_hire", "Venue Hire"),
    ("insurance", "Insurance"),
    ("supplies", "Supplies"),
    ("maintenance", "Maintenance"),
    ("travel", "Travel"),
    ("affiliation_fees", "Affiliation Fees"),
    ("coaching", "Coaching"),
    ("payment_processing_fees", "Payment Processing Fees"),
    ("other", "Other"),
]

INCOME_CATEGORIES = [
    ("membership_fees", "Membership Fees"),
    ("shoot_fees", "Shoot Fees"),
    ("equipment_sales", "Equipment Sales"),
    ("donations", "Donations"),
    ("sponsorship", "Sponsorship"),
    ("grants", "Grants"),
    ("fundraising", "Fundraising"),
    ("other", "Other"),
]


class FinancialTransaction(db.Model):
    __tablename__ = "financial_transactions"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum("income", "expense"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), default="EUR")
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255), nullable=True)
    receipt_reference = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")

    @property
    def amount(self):
        return self.amount_cents / 100.0

    @amount.setter
    def amount(self, value):
        self.amount_cents = int(round(value * 100))

    def __repr__(self):
        return f"<FinancialTransaction {self.id} type={self.type} amount={self.amount}>"
