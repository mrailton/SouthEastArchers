from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Model
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Membership(Model):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_credits: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    purchased_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    user: Mapped[User] = relationship("User", back_populates="membership")

    def is_active(self) -> bool:
        return self.status == "active" and self.expiry_date >= date.today()

    def credits_remaining(self) -> int:
        """Return total credits available (initial + purchased)."""
        initial = self.initial_credits if self.initial_credits is not None else 0
        purchased = self.purchased_credits if self.purchased_credits is not None else 0
        return initial + purchased

    def use_credit(self, allow_negative: bool = False) -> bool:
        """Use a credit from the membership.

        Uses initial credits first, then purchased credits.

        Args:
            allow_negative: If True, allows credits to go negative (e.g., for admin bookings)

        Returns:
            True if credit was used, False if no credits available and negative not allowed
        """
        initial = self.initial_credits if self.initial_credits is not None else 0
        purchased = self.purchased_credits if self.purchased_credits is not None else 0

        total_credits = initial + purchased

        if total_credits > 0:
            if initial > 0:
                self.initial_credits = initial - 1
            else:
                self.purchased_credits = purchased - 1
            return True
        elif allow_negative and self.is_active():
            self.initial_credits = initial - 1
            return True
        return False

    def add_credits(self, amount: int) -> None:
        """Add purchased credits to the membership."""
        current = self.purchased_credits if self.purchased_credits is not None else 0
        self.purchased_credits = current + amount

    def remove_credits(self, amount: int) -> None:
        """Remove credits from the membership, taking from initial credits first."""
        initial = self.initial_credits if self.initial_credits is not None else 0
        purchased = self.purchased_credits if self.purchased_credits is not None else 0

        remaining = amount
        deduct_initial = min(remaining, max(initial, 0))
        self.initial_credits = initial - deduct_initial
        remaining -= deduct_initial
        if remaining > 0:
            self.purchased_credits = purchased - remaining

    def renew(self, expiry_date: date, initial_credits: int = 20) -> None:
        """Renew the membership."""
        self.start_date = date.today()
        self.expiry_date = expiry_date
        self.initial_credits = initial_credits
        self.status = "active"

    def expire_initial_credits(self) -> None:
        """Expire initial credits but retain purchased credits."""
        self.initial_credits = 0

    def activate(self) -> None:
        self.status = "active"

    def deactivate(self) -> None:
        self.status = "inactive"

    def __repr__(self) -> str:
        return f"<Membership user_id={self.user_id} initial={self.initial_credits} purchased={self.purchased_credits}>"
