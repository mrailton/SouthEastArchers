from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Model
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.user import User

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
    __table_args__ = (
        UniqueConstraint(
            "receipt_reference",
            "category",
            "type",
            name="uq_financial_txn_receipt_category_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(Enum("income", "expense"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    created_by: Mapped[User] = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    @property
    def amount(self) -> float:
        return self.amount_cents / 100.0

    def __repr__(self) -> str:
        return f"<FinancialTransaction {self.id} type={self.type} amount={self.amount}>"
