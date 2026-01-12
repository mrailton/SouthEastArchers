from functools import wraps
from typing import Any, Callable, TypeVar

from flask import Response, abort, flash, redirect, url_for
from flask_login import current_user

F = TypeVar("F", bound=Callable[..., Any])


def admin_required(f: F) -> F:
    """Decorator to require admin authentication."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response | Any:
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            flash("You do not have permission to access this page.", "error")
            abort(403)

        return f(*args, **kwargs)

    return decorated_function  # type: ignore[return-value]
