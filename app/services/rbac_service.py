from __future__ import annotations

from collections.abc import Iterable

from app.models import Permission, Role
from app.repositories import RBACRepository
from app.services.result import ServiceResult


class RBACService:
    @staticmethod
    def list_roles() -> list[Role]:
        return RBACRepository.list_roles()

    @staticmethod
    def list_permissions() -> list[Permission]:
        return RBACRepository.list_permissions()

    @staticmethod
    def get_role(role_id: int) -> Role | None:
        return RBACRepository.get_role(role_id)

    @staticmethod
    def create_role(name: str, description: str | None, permission_ids: Iterable[int]) -> ServiceResult[Role]:
        if RBACRepository.role_name_exists(name):
            return ServiceResult.fail("Role name already exists.")

        role = Role(name=name, description=description or "")
        perms = RBACRepository.get_permissions_by_ids(permission_ids or [])
        role.permissions = perms  # type: ignore[assignment]
        try:
            RBACRepository.add_role(role)
            RBACRepository.save()
            return ServiceResult.ok(data=role)
        except Exception as exc:
            return ServiceResult.fail(f"Error creating role: {exc}")

    @staticmethod
    def update_role(role: Role, name: str, description: str | None, permission_ids: Iterable[int]) -> ServiceResult[None]:
        if RBACRepository.role_name_exists(name, exclude_id=role.id):
            return ServiceResult.fail("Role name already exists.")

        role.name = name
        role.description = description or ""
        perms = RBACRepository.get_permissions_by_ids(permission_ids or [])
        role.permissions = perms  # type: ignore[assignment]
        try:
            RBACRepository.save()
            return ServiceResult.ok(message="Role updated successfully.")
        except Exception as exc:
            return ServiceResult.fail(f"Error updating role: {exc}")

    @staticmethod
    def delete_role(role: Role) -> ServiceResult[None]:
        try:
            RBACRepository.delete_role(role)
            RBACRepository.save()
            return ServiceResult.ok(message="Role deleted.")
        except Exception as exc:
            return ServiceResult.fail(f"Error deleting role: {exc}")
