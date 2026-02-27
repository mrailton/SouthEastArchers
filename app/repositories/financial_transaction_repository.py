"""Repository for FinancialTransaction model data access."""

from __future__ import annotations

from datetime import date

from app import db
from app.models import FinancialTransaction
from app.repositories.base import BaseRepository


class FinancialTransactionRepository(BaseRepository):
    @staticmethod
    def get_by_id(transaction_id: int) -> FinancialTransaction | None:
        return db.session.get(FinancialTransaction, transaction_id)

    @staticmethod
    def get_all() -> list[FinancialTransaction]:
        return FinancialTransaction.query.order_by(FinancialTransaction.date.desc(), FinancialTransaction.created_at.desc()).all()

    @staticmethod
    def get_all_paginated(page: int = 1, per_page: int = 20):
        """Return a paginated query ordered by date descending, then created_at descending."""
        return FinancialTransaction.query.order_by(FinancialTransaction.date.desc(), FinancialTransaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_by_type(txn_type: str) -> list[FinancialTransaction]:
        return FinancialTransaction.query.filter_by(type=txn_type).order_by(FinancialTransaction.date.desc(), FinancialTransaction.created_at.desc()).all()

    @staticmethod
    def get_by_date_range(
        start_date: date,
        end_date: date,
        txn_type: str | None = None,
    ) -> list[FinancialTransaction]:
        query = FinancialTransaction.query.filter(
            FinancialTransaction.date >= start_date,
            FinancialTransaction.date <= end_date,
        )
        if txn_type:
            query = query.filter_by(type=txn_type)
        return query.order_by(FinancialTransaction.date.desc(), FinancialTransaction.created_at.desc()).all()

    @staticmethod
    def add(transaction: FinancialTransaction) -> None:
        db.session.add(transaction)

    @staticmethod
    def delete(transaction: FinancialTransaction) -> None:
        db.session.delete(transaction)
