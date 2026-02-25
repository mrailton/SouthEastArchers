"""Repository for Payment model data access."""

from __future__ import annotations

from app import db
from app.models import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    @staticmethod
    def get_by_id(payment_id: int) -> Payment | None:
        return db.session.get(Payment, payment_id)

    @staticmethod
    def get_by_user(user_id: int) -> list[Payment]:
        return Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()

    @staticmethod
    def get_pending_cash() -> list[Payment]:
        return Payment.query.filter_by(payment_method="cash", status="pending").order_by(Payment.created_at.desc()).all()

    @staticmethod
    def count_pending_cash() -> int:
        return Payment.query.filter_by(payment_method="cash", status="pending").count()

    @staticmethod
    def get_pending_cash_limited(limit: int = 5) -> list[Payment]:
        return Payment.query.filter_by(payment_method="cash", status="pending").order_by(Payment.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_pending_cash_for_user(user_id: int, payment_type: str = "membership") -> Payment | None:
        return Payment.query.filter_by(
            user_id=user_id,
            payment_type=payment_type,
            payment_method="cash",
            status="pending",
        ).first()

    @staticmethod
    def get_completed_for_user(user_id: int, payment_type: str = "membership") -> Payment | None:
        return Payment.query.filter_by(
            user_id=user_id,
            payment_type=payment_type,
            status="completed",
        ).first()

    @staticmethod
    def get_by_user_and_type(user_id: int, payment_type: str) -> Payment | None:
        return Payment.query.filter_by(user_id=user_id, payment_type=payment_type).first()

    @staticmethod
    def add(payment: Payment) -> None:
        db.session.add(payment)

    @staticmethod
    def delete(payment: Payment) -> None:
        db.session.delete(payment)
