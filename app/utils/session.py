"""Session utility functions"""

from flask import session


def get_user_id_from_session(current_user):
    """Get user ID from various session keys or current user"""
    return (
        session.get("signup_user_id")
        or session.get("membership_renewal_user_id")
        or session.get("credit_purchase_user_id")
        or (current_user.id if current_user.is_authenticated else None)
    )


def clear_session_keys(*keys):
    """Clear multiple session keys"""
    for key in keys:
        session.pop(key, None)
