"""Repository for User model data access."""

from __future__ import annotations

from app import db
from app.models import User
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
    def get_recent(limit: int = 5) -> list[User]:
        return User.query.order_by(User.created_at.desc()).limit(limit).all()

    @staticmethod
    def count() -> int:
        return User.query.count()

    @staticmethod
    def count_pending_users() -> int:
        return User.query.filter_by(is_active=False).count()

    @staticmethod
    def get_active_with_membership() -> list[User]:
        return User.query.filter_by(is_active=True).order_by(User.name).all()

    @staticmethod
    def get_all_with_permission(permission_name: str) -> list[User]:
        """Get all users that have a specific permission via any of their roles."""
        from app.models import Permission

        perm = Permission.query.filter_by(name=permission_name).first()
        if not perm:
            return []
        return [user for user in User.query.all() if any(any(p.id == perm.id for p in role.permissions) for role in user.roles)]

    @staticmethod
    def add(user: User) -> None:
        db.session.add(user)

    @staticmethod
    def delete(user: User) -> None:
        db.session.delete(user)
