"""Repository for Membership model data access."""

from __future__ import annotations

from datetime import date

from app import db
from app.models import Membership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository):
    @staticmethod
    def count_active() -> int:
        return Membership.query.filter_by(status="active").count()

    @staticmethod
    def get_expired() -> list[Membership]:
        return Membership.query.filter(
            Membership.status == "active",
            Membership.expiry_date < date.today(),
        ).all()

    @staticmethod
    def add(membership: Membership) -> None:
        db.session.add(membership)
