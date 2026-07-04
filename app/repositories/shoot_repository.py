"""Repository for Shoot model data access."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.db import Pagination, db, paginate
from app.models import Shoot
from app.repositories.base import BaseRepository


class ShootRepository(BaseRepository):
    @staticmethod
    def get_by_id(shoot_id: int) -> Shoot | None:
        return db.session.get(Shoot, shoot_id)

    @staticmethod
    def get_all() -> list[Shoot]:
        stmt = select(Shoot).order_by(Shoot.date.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_upcoming() -> list[Shoot]:
        stmt = select(Shoot).where(Shoot.date >= date.today()).order_by(Shoot.date.asc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def count_upcoming() -> int:
        stmt = select(func.count()).select_from(Shoot).where(Shoot.date >= date.today())
        return db.session.scalar(stmt) or 0

    @staticmethod
    def get_all_paginated(page: int = 1, per_page: int = 10) -> Pagination:
        stmt = select(Shoot).order_by(Shoot.date.desc())
        return paginate(db.session, stmt, page=page, per_page=per_page)

    @staticmethod
    def add(shoot: Shoot) -> None:
        db.session.add(shoot)
