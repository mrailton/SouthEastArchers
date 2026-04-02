"""Repository for Shoot model data access."""

from __future__ import annotations

from app import db
from app.models import Shoot
from app.repositories.base import BaseRepository
from app.utils.datetime_utils import utc_now


class ShootRepository(BaseRepository):
    @staticmethod
    def get_by_id(shoot_id: int) -> Shoot | None:
        return db.session.get(Shoot, shoot_id)

    @staticmethod
    def get_all() -> list[Shoot]:
        return Shoot.query.order_by(Shoot.date.desc()).all()

    @staticmethod
    def get_upcoming() -> list[Shoot]:
        return Shoot.query.filter(Shoot.date > utc_now()).order_by(Shoot.date.desc()).all()

    @staticmethod
    def count_upcoming() -> int:
        return Shoot.query.filter(Shoot.date > utc_now()).count()

    @staticmethod
    def get_all_paginated(page: int = 1, per_page: int = 10):
        return Shoot.query.order_by(Shoot.date.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def add(shoot: Shoot) -> None:
        db.session.add(shoot)
