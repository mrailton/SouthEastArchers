"""Repository for FinancialTransaction model data access."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.db import Pagination, db, paginate
from app.models import FinancialTransaction
from app.repositories.base import BaseRepository


class FinancialTransactionRepository(BaseRepository):
    @staticmethod
    def get_by_id(transaction_id: int) -> FinancialTransaction | None:
        return db.session.get(FinancialTransaction, transaction_id)

    @staticmethod
    def get_all_paginated(page: int = 1, per_page: int = 20) -> Pagination:
        stmt = select(FinancialTransaction).order_by(
            FinancialTransaction.date.desc(),
            FinancialTransaction.created_at.desc(),
        )
        return paginate(db.session, stmt, page=page, per_page=per_page)

    @staticmethod
    def get_by_date_range(
        start_date: date,
        end_date: date,
        txn_type: str | None = None,
    ) -> list[FinancialTransaction]:
        stmt = select(FinancialTransaction).where(
            FinancialTransaction.date >= start_date,
            FinancialTransaction.date <= end_date,
        )
        if txn_type:
            stmt = stmt.where(FinancialTransaction.type == txn_type)
        stmt = stmt.order_by(FinancialTransaction.date.desc(), FinancialTransaction.created_at.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(transaction: FinancialTransaction) -> None:
        db.session.add(transaction)

    @staticmethod
    def delete(transaction: FinancialTransaction) -> None:
        db.session.delete(transaction)
