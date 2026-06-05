from __future__ import annotations

from fastapi import Request

from app.models.user import User


def get_user_id_from_session(request: Request, user: User | None) -> int | None:
    return (
        request.session.get("signup_user_id")
        or request.session.get("membership_renewal_user_id")
        or request.session.get("credit_purchase_user_id")
        or (user.id if user is not None else None)
    )


def clear_session_keys(request: Request, *keys: str) -> None:
    for key in keys:
        request.session.pop(key, None)
