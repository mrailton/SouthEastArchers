"""Repository for Membership model data access."""

from __future__ import annotations

from datetime import date, timedelta

from app import db
from app.models import Membership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository):
    @staticmethod
    def get_by_id(membership_id: int) -> Membership | None:
        return db.session.get(Membership, membership_id)

    @staticmethod
    def get_by_user_id(user_id: int) -> Membership | None:
        return Membership.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_active() -> list[Membership]:
        return Membership.query.filter_by(status="active").all()

    @staticmethod
    def count_active() -> int:
        return Membership.query.filter_by(status="active").count()

    @staticmethod
    def get_expiring_soon(days: int = 30) -> list[Membership]:
        cutoff_date = date.today() + timedelta(days=days)
        return Membership.query.filter(
            Membership.status == "active",
            Membership.expiry_date <= cutoff_date,
        ).all()

    @staticmethod
    def count_expiring_soon(days: int = 30) -> int:
        today = date.today()
        cutoff_date = today + timedelta(days=days)
        return Membership.query.filter(
            Membership.status == "active",
            Membership.expiry_date <= cutoff_date,
            Membership.expiry_date >= today,
        ).count()

    @staticmethod
    def get_expired() -> list[Membership]:
        return Membership.query.filter(
            Membership.status == "active",
            Membership.expiry_date < date.today(),
        ).all()

    @staticmethod
    def add(membership: Membership) -> None:
        db.session.add(membership)
