from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser
from app.policies import require_all_permissions
from app.templating import flash

F = TypeVar("F", bound=Callable)


def require_perms(*permission_names: str):
    async def _dependency(user: CurrentUser) -> CurrentUser:
        require_all_permissions(user, *permission_names)
        return user

    return Depends(_dependency)


def redirect_back(request: Request, default: str) -> str:
    target = request.query_params.get("next") or default
    if not target.startswith("/"):
        return default
    return target


def flash_form_errors(request: Request, form) -> None:
    for field, errors in form.errors.items():
        for error in errors:
            flash(request, "error", f"{field}: {error}")


def flash_service_warnings(request: Request, result) -> None:
    for message in getattr(result, "warnings", []) or []:
        flash(request, "warning", f"Warning: {message}")


def redirect_with_flash(request: Request, url: str, category: str, message: str) -> RedirectResponse:
    flash(request, category, message)
    return RedirectResponse(url=url, status_code=303)
