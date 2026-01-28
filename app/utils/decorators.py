from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any, TypeVar

from flask import Response, abort, flash, redirect, url_for
from flask_login import current_user

F = TypeVar("F", bound=Callable[..., Any])


def permission_required(*permissions: str) -> Callable[[F], F]:
    """Decorator to require all listed permissions for a route."""

    def decorator(f: F) -> F:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Response | Any:
            if not current_user.is_authenticated:
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))

            missing = [perm for perm in permissions if not getattr(current_user, "has_permission", lambda _p: False)(perm)]
            if missing:
                flash("You do not have permission to access this page.", "error")
                abort(403)

            return f(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator


def any_permission_required(permissions: Iterable[str]) -> Callable[[F], F]:
    """Decorator to require at least one permission from the provided iterable."""

    perms = list(permissions)

    def decorator(f: F) -> F:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Response | Any:
            if not current_user.is_authenticated:
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))

            has_perm = getattr(current_user, "has_any_permission", lambda *args: False)(*perms)
            if not has_perm:
                flash("You do not have permission to access this page.", "error")
                abort(403)

            return f(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator


# Backwards compatibility alias for existing imports
admin_required = permission_required("admin.dashboard.view")
