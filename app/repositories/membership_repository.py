"""Repository for Membership model data access."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.db import db
from app.models import Membership, User
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository):
    @staticmethod
    def count_active() -> int:
        stmt = select(func.count()).select_from(Membership).where(Membership.status == "active")
        return db.session.scalar(stmt) or 0

    @staticmethod
    def get_expired() -> list[Membership]:
        stmt = select(Membership).where(
            Membership.status == "active",
            Membership.expiry_date < date.today(),
        )
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_active_for_active_users() -> list[Membership]:
        stmt = select(Membership).options(joinedload(Membership.user)).join(User).where(Membership.status == "active", User.is_active.is_(True))
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(membership: Membership) -> None:
        db.session.add(membership)
