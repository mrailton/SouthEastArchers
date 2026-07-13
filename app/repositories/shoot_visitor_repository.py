"""Repository for ShootVisitor model data access."""

from __future__ import annotations

from sqlalchemy import select

from app.db import db
from app.models import ShootVisitor
from app.repositories.base import BaseRepository


class ShootVisitorRepository(BaseRepository):
    @staticmethod
    def get_by_shoot_id(shoot_id: int) -> list[ShootVisitor]:
        stmt = select(ShootVisitor).where(ShootVisitor.shoot_id == shoot_id)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(visitor: ShootVisitor) -> None:
        db.session.add(visitor)

    @staticmethod
    def delete(visitor: ShootVisitor) -> None:
        db.session.delete(visitor)
