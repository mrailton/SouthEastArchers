"""Repository for Credit model data access."""

from __future__ import annotations

from app import db
from app.models import Credit
from app.repositories.base import BaseRepository


class CreditRepository(BaseRepository):
    @staticmethod
    def get_by_id(credit_id: int) -> Credit | None:
        return db.session.get(Credit, credit_id)

    @staticmethod
    def get_by_user(user_id: int) -> list[Credit]:
        return Credit.query.filter_by(user_id=user_id).all()

    @staticmethod
    def add(credit: Credit) -> None:
        db.session.add(credit)
