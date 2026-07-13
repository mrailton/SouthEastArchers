"""Repository for Role and Permission model data access."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select

from app.db import db
from app.models import Permission, Role
from app.repositories.base import BaseRepository


class RBACRepository(BaseRepository):
    @staticmethod
    def seed() -> None:
        """Idempotently seed default roles and permissions."""
        from app.models.rbac import seed_rbac

        seed_rbac(db.session)  # type: ignore[arg-type]

    @staticmethod
    def get_role(role_id: int) -> Role | None:
        return db.session.get(Role, role_id)

    @staticmethod
    def get_role_by_name(name: str) -> Role | None:
        return db.session.scalars(select(Role).where(Role.name == name)).first()

    @staticmethod
    def list_roles() -> list[Role]:
        stmt = select(Role).order_by(Role.name)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def role_name_exists(name: str, exclude_id: int | None = None) -> bool:
        stmt = select(Role).where(Role.name == name)
        if exclude_id is not None:
            stmt = stmt.where(Role.id != exclude_id)
        return db.session.scalars(stmt).first() is not None

    @staticmethod
    def add_role(role: Role) -> None:
        db.session.add(role)

    @staticmethod
    def delete_role(role: Role) -> None:
        db.session.delete(role)

    @staticmethod
    def list_permissions() -> list[Permission]:
        stmt = select(Permission).order_by(Permission.name)
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_permissions_by_ids(ids: Iterable[int]) -> list[Permission]:
        if not ids:
            return []
        stmt = select(Permission).where(Permission.id.in_(list(ids)))
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_roles_by_ids(ids: Iterable[int]) -> list[Role]:
        if not ids:
            return []
        stmt = select(Role).where(Role.id.in_(list(ids)))
        return list(db.session.scalars(stmt).unique().all())
