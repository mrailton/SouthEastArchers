from __future__ import annotations

from collections.abc import Iterable

from app import db
from app.models import Permission, Role


class RBACService:
    @staticmethod
    def list_roles() -> list[Role]:
        return Role.query.order_by(Role.name).all()

    @staticmethod
    def list_permissions() -> list[Permission]:
        return Permission.query.order_by(Permission.name).all()

    @staticmethod
    def get_role(role_id: int) -> Role | None:
        return db.session.get(Role, role_id)

    @staticmethod
    def create_role(name: str, description: str | None, permission_ids: Iterable[int]) -> tuple[Role | None, str | None]:
        if Role.query.filter_by(name=name).first():
            return None, "Role name already exists."

        role = Role(name=name, description=description or "")
        perms = Permission.query.filter(Permission.id.in_(permission_ids or [])).all()
        role.permissions = perms
        try:
            db.session.add(role)
            db.session.commit()
            return role, None
        except Exception as exc:  # pragma: no cover - defensive
            db.session.rollback()
            return None, f"Error creating role: {exc}"

    @staticmethod
    def update_role(role: Role, name: str, description: str | None, permission_ids: Iterable[int]) -> tuple[bool, str]:
        # Ensure name uniqueness
        existing = Role.query.filter(Role.name == name, Role.id != role.id).first()
        if existing:
            return False, "Role name already exists."

        role.name = name
        role.description = description or ""
        perms = Permission.query.filter(Permission.id.in_(permission_ids or [])).all()
        role.permissions = perms
        try:
            db.session.commit()
            return True, "Role updated successfully."
        except Exception as exc:  # pragma: no cover - defensive
            db.session.rollback()
            return False, f"Error updating role: {exc}"

    @staticmethod
    def delete_role(role: Role) -> tuple[bool, str]:
        try:
            db.session.delete(role)
            db.session.commit()
            return True, "Role deleted."
        except Exception as exc:  # pragma: no cover - defensive
            db.session.rollback()
            return False, f"Error deleting role: {exc}"
