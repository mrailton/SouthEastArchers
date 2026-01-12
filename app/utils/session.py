from typing import Any

from flask import session


def get_user_id_from_session(current_user: Any) -> int | None:
    """Get user ID from session or current user."""
    return (
        session.get("signup_user_id")
        or session.get("membership_renewal_user_id")
        or session.get("credit_purchase_user_id")
        or (current_user.id if current_user.is_authenticated else None)
    )


def clear_session_keys(*keys: str) -> None:
    """Clear specified keys from session."""
    for key in keys:
        session.pop(key, None)
