from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Model
from app.enums import PaymentMethod, PaymentType
from app.utils.datetime_utils import utc_now


class Payment(Model):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=PaymentMethod.ONLINE,
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "completed", "failed", "cancelled"),
        default="pending",
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    payment_processor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_transaction_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    user: Mapped[User] = relationship("User", back_populates="payments")

    def mark_completed(self, transaction_id: str | None = None, processor: str | None = None) -> None:
        self.status = "completed"
        self.external_transaction_id = transaction_id
        self.payment_processor = processor

    def mark_failed(self) -> None:
        self.status = "failed"

    @property
    def amount(self) -> float:
        return self.amount_cents / 100.0

    @amount.setter
    def amount(self, value: float) -> None:
        self.amount_cents = int(round(value * 100))

    def __repr__(self) -> str:
        return f"<Payment {self.id} user_id={self.user_id} {self.status}>"
