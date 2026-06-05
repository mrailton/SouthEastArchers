"""Repository for Payment model data access."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.db import db, paginate
from app.db.pagination import Pagination
from app.enums import PaymentMethod, PaymentType
from app.models import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    @staticmethod
    def get_by_id(payment_id: int) -> Payment | None:
        return db.session.get(Payment, payment_id)

    @staticmethod
    def get_by_id_with_user(payment_id: int) -> Payment | None:
        stmt = select(Payment).options(joinedload(Payment.user)).where(Payment.id == payment_id)
        return db.session.scalars(stmt).unique().first()

    @staticmethod
    def get_by_user(user_id: int) -> list[Payment]:
        stmt = select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_by_user_paginated(user_id: int, page: int = 1, per_page: int = 5) -> Pagination:
        stmt = select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
        return paginate(db.session, stmt, page=page, per_page=per_page)

    @staticmethod
    def get_pending_cash() -> list[Payment]:
        stmt = select(Payment).where(Payment.payment_method == PaymentMethod.CASH, Payment.status == "pending").order_by(Payment.created_at.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def count_pending_cash() -> int:
        stmt = (
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.payment_method == PaymentMethod.CASH,
                Payment.status == "pending",
            )
        )
        return db.session.scalar(stmt) or 0

    @staticmethod
    def get_pending_cash_limited(limit: int = 5) -> list[Payment]:
        stmt = select(Payment).where(Payment.payment_method == PaymentMethod.CASH, Payment.status == "pending").order_by(Payment.created_at.desc()).limit(limit)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_pending_cash_with_users() -> list[dict]:
        stmt = (
            select(Payment)
            .options(joinedload(Payment.user))
            .where(Payment.payment_method == PaymentMethod.CASH, Payment.status == "pending")
            .order_by(Payment.created_at.desc())
        )
        payments = db.session.scalars(stmt).unique().all()
        return [{"payment": payment, "user": payment.user} for payment in payments]

    @staticmethod
    def get_pending_cash_limited_with_users(limit: int = 5) -> list[dict]:
        stmt = (
            select(Payment)
            .options(joinedload(Payment.user))
            .where(Payment.payment_method == PaymentMethod.CASH, Payment.status == "pending")
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        payments = db.session.scalars(stmt).unique().all()
        return [{"payment": payment, "user": payment.user} for payment in payments]

    @staticmethod
    def get_pending_by_sumup_checkout_id(checkout_id: str) -> Payment | None:
        stmt = select(Payment).where(
            Payment.sumup_checkout_id == checkout_id,
            Payment.status == "pending",
            Payment.payment_method == PaymentMethod.ONLINE,
        )
        return db.session.scalars(stmt).first()

    @staticmethod
    def get_pending_online_with_users() -> list[dict]:
        stmt = (
            select(Payment)
            .options(joinedload(Payment.user))
            .where(
                Payment.payment_method == PaymentMethod.ONLINE,
                Payment.status == "pending",
                Payment.sumup_checkout_id.is_not(None),
            )
            .order_by(Payment.created_at.desc())
        )
        payments = db.session.scalars(stmt).unique().all()
        return [{"payment": payment, "user": payment.user} for payment in payments]

    @staticmethod
    def get_pending_cash_for_user(user_id: int, payment_type: str = PaymentType.MEMBERSHIP) -> Payment | None:
        stmt = select(Payment).where(
            Payment.user_id == user_id,
            Payment.payment_type == payment_type,
            Payment.payment_method == PaymentMethod.CASH,
            Payment.status == "pending",
        )
        return db.session.scalars(stmt).first()

    @staticmethod
    def get_completed_for_user(user_id: int, payment_type: str = PaymentType.MEMBERSHIP) -> Payment | None:
        stmt = select(Payment).where(
            Payment.user_id == user_id,
            Payment.payment_type == payment_type,
            Payment.status == "completed",
        )
        return db.session.scalars(stmt).first()

    @staticmethod
    def add(payment: Payment) -> None:
        db.session.add(payment)

    @staticmethod
    def delete(payment: Payment) -> None:
        db.session.delete(payment)
