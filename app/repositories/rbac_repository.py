"""Repository for Role and Permission model data access."""

from __future__ import annotations

from collections.abc import Iterable

from app import db
from app.models import Permission, Role
from app.repositories.base import BaseRepository


class RBACRepository(BaseRepository):
    # --- Role ---
    @staticmethod
    def get_role(role_id: int) -> Role | None:
        return db.session.get(Role, role_id)

    @staticmethod
    def get_role_by_name(name: str) -> Role | None:
        return Role.query.filter_by(name=name).first()

    @staticmethod
    def list_roles() -> list[Role]:
        return Role.query.order_by(Role.name).all()

    @staticmethod
    def role_name_exists(name: str, exclude_id: int | None = None) -> bool:
        query = Role.query.filter(Role.name == name)
        if exclude_id is not None:
            query = query.filter(Role.id != exclude_id)
        return query.first() is not None

    @staticmethod
    def add_role(role: Role) -> None:
        db.session.add(role)

    @staticmethod
    def delete_role(role: Role) -> None:
        db.session.delete(role)

    # --- Permission ---
    @staticmethod
    def get_permission_by_name(name: str) -> Permission | None:
        return Permission.query.filter_by(name=name).first()

    @staticmethod
    def list_permissions() -> list[Permission]:
        return Permission.query.order_by(Permission.name).all()

    @staticmethod
    def get_permissions_by_ids(ids: Iterable[int]) -> list[Permission]:
        return Permission.query.filter(Permission.id.in_(ids or [])).all()

    @staticmethod
    def get_roles_by_ids(ids: Iterable[int]) -> list[Role]:
        return Role.query.filter(Role.id.in_(ids or [])).all()

    @staticmethod
    def add_permission(permission: Permission) -> None:
        db.session.add(permission)
