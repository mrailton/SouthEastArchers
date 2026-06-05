"""Repository for User model data access."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from app.db import Pagination, db, paginate
from app.models import Permission, Role, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_id_with_permissions(user_id: int) -> User | None:
        stmt = select(User).options(joinedload(User.roles).joinedload(Role.permissions)).where(User.id == user_id)
        return db.session.scalars(stmt).unique().first()

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return db.session.scalars(select(User).where(User.email == email)).first()

    @staticmethod
    def get_by_ids_with_membership(user_ids: list[int]) -> dict[int, User]:
        if not user_ids:
            return {}
        stmt = select(User).options(joinedload(User.membership)).where(User.id.in_(user_ids))
        users = db.session.scalars(stmt).unique().all()
        return {user.id: user for user in users}

    @staticmethod
    def get_all(order_by_name: bool = True) -> list[User]:
        stmt = select(User)
        if order_by_name:
            stmt = stmt.order_by(User.name)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_all_paginated(page: int = 1, per_page: int = 20, search: str = "", membership_filter: str = "all") -> Pagination:
        stmt = select(User).options(joinedload(User.membership), joinedload(User.roles))
        if search:
            term = f"%{search}%"
            stmt = stmt.where(or_(User.name.ilike(term), User.email.ilike(term), User.phone.ilike(term)))
        if membership_filter == "with":
            stmt = stmt.where(User.membership.has())
        elif membership_filter == "without":
            stmt = stmt.where(~User.membership.has())
        stmt = stmt.order_by(User.name)
        return paginate(db.session, stmt, page=page, per_page=per_page)

    @staticmethod
    def get_recent(limit: int = 5) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def count() -> int:
        return db.session.scalar(select(func.count()).select_from(User)) or 0

    @staticmethod
    def count_admins() -> int:
        stmt = select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(Role.name == "Admin")
        return db.session.scalar(stmt) or 0

    @staticmethod
    def count_pending_users() -> int:
        stmt = select(func.count()).select_from(User).where(User.is_active.is_(False))
        return db.session.scalar(stmt) or 0

    @staticmethod
    def get_active_with_membership() -> list[User]:
        stmt = select(User).options(joinedload(User.membership)).where(User.is_active.is_(True)).order_by(User.name)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_all_with_permission(permission_name: str) -> list[User]:
        stmt = select(User).join(User.roles).join(Role.permissions).where(Permission.name == permission_name).distinct()
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(user: User) -> None:
        db.session.add(user)

    @staticmethod
    def delete(user: User) -> None:
        db.session.delete(user)
