"""Repository for Credit model data access."""

from __future__ import annotations

from sqlalchemy import select

from app.db import db
from app.models import Credit
from app.repositories.base import BaseRepository


class CreditRepository(BaseRepository):
    @staticmethod
    def get_by_user(user_id: int) -> list[Credit]:
        stmt = select(Credit).where(Credit.user_id == user_id)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(credit: Credit) -> None:
        db.session.add(credit)
