"""Repository for Shoot model data access."""

from __future__ import annotations

from app import db
from app.models import Shoot
from app.repositories.base import BaseRepository


class ShootRepository(BaseRepository):
    @staticmethod
    def get_by_id(shoot_id: int) -> Shoot | None:
        return db.session.get(Shoot, shoot_id)

    @staticmethod
    def get_all() -> list[Shoot]:
        return Shoot.query.order_by(Shoot.date.desc()).all()

    @staticmethod
    def add(shoot: Shoot) -> None:
        db.session.add(shoot)
