"""Repository for User model data access."""

from __future__ import annotations

from flask_sqlalchemy.pagination import Pagination

from app import db
from app.models import Permission, Role, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_all(order_by_name: bool = True) -> list[User]:
        query = User.query
        if order_by_name:
            query = query.order_by(User.name)
        return query.all()

    @staticmethod
    def get_all_paginated(page: int = 1, per_page: int = 20, search: str = "", membership_filter: str = "all") -> Pagination:

        query = User.query
        if search:
            term = f"%{search}%"
            query = query.filter(db.or_(User.name.ilike(term), User.email.ilike(term), User.phone.ilike(term)))
        if membership_filter == "with":
            query = query.filter(User.membership.has())
        elif membership_filter == "without":
            query = query.filter(~User.membership.has())
        return query.order_by(User.name).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_recent(limit: int = 5) -> list[User]:
        return User.query.order_by(User.created_at.desc()).limit(limit).all()

    @staticmethod
    def count() -> int:
        return User.query.count()

    @staticmethod
    def count_admins() -> int:

        return db.session.query(User).join(User.roles).filter(Role.name == "Admin").distinct().count()

    @staticmethod
    def count_pending_users() -> int:
        return User.query.filter_by(is_active=False).count()

    @staticmethod
    def get_active_with_membership() -> list[User]:
        return User.query.filter_by(is_active=True).order_by(User.name).all()

    @staticmethod
    def get_all_with_permission(permission_name: str) -> list[User]:
        """Get all users that have a specific permission via any of their roles."""
        return User.query.join(User.roles).join(Role.permissions).filter(Permission.name == permission_name).distinct().all()

    @staticmethod
    def add(user: User) -> None:
        db.session.add(user)

    @staticmethod
    def delete(user: User) -> None:
        db.session.delete(user)
