from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Model
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


class FinancialTransaction(Model):
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True)
    type = Column(Enum("income", "expense"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="EUR")
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    receipt_reference = Column(String(255), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    @property
    def amount(self) -> float:
        return self.amount_cents / 100.0

    def __repr__(self) -> str:
        return f"<FinancialTransaction {self.id} type={self.type} amount={self.amount}>"
