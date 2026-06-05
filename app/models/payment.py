from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from app.db import Model, db
from app.enums import PaymentMethod, PaymentType
from app.utils.datetime_utils import utc_now


class Payment(Model):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="EUR")
    payment_type = Column(Enum(PaymentType, values_callable=lambda e: [m.value for m in e]), nullable=False)
    payment_method = Column(Enum(PaymentMethod, values_callable=lambda e: [m.value for m in e]), nullable=False, default=PaymentMethod.ONLINE)
    status = Column(
        Enum("pending", "completed", "failed", "cancelled"),
        default="pending",
        index=True,
    )
    description = Column(Text)
    payment_processor = Column(String(50), nullable=True)
    external_transaction_id = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

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
