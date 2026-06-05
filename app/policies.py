"""Permission-based access control for FastAPI routes."""

from __future__ import annotations

from app.exceptions import AuthorizationError, LoginRequired
from app.models.user import User


def has_permission(user: User | None, permission_name: str) -> bool:
    if user is None:
        return False
    return user.has_permission(permission_name)


def has_any_permission(user: User | None, *permission_names: str) -> bool:
    if user is None or not permission_names:
        return False
    return user.has_any_permission(*permission_names)


def require_permission(user: User | None, *permission_names: str) -> None:
    """Require the user to have at least one of the given permissions."""
    if user is None:
        raise LoginRequired()
    if permission_names and not user.has_any_permission(*permission_names):
        raise AuthorizationError(f"Missing required permission(s): {', '.join(permission_names)}")


def require_all_permissions(user: User | None, *permission_names: str) -> None:
    if user is None:
        raise LoginRequired()
    missing = [name for name in permission_names if not user.has_permission(name)]
    if missing:
        raise AuthorizationError(f"Missing required permission(s): {', '.join(missing)}")
