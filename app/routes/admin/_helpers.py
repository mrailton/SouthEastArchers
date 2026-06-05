from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse

from app.templating import flash


def redirect_back(request: Request, default: str) -> str:
    target = request.query_params.get("next") or default
    if not target.startswith("/"):
        return default
    return target


def flash_form_errors(request: Request, form_or_errors) -> None:
    errors = form_or_errors.errors if hasattr(form_or_errors, "errors") else form_or_errors
    for field, field_errors in errors.items():
        for error in field_errors:
            flash(request, "error", f"{field}: {error}")


def flash_service_warnings(request: Request, result) -> None:
    for message in getattr(result, "warnings", []) or []:
        flash(request, "warning", f"Warning: {message}")


def redirect_with_flash(request: Request, url: str, category: str, message: str) -> RedirectResponse:
    flash(request, category, message)
    return RedirectResponse(url=url, status_code=303)
