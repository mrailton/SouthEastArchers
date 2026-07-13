from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from fastapi import Request

from app.models.user import User

_MEMBERSHIP_RENEWAL_KEYS = ("membership_renewal_user_id", "membership_renewal_payment_id")
_CREDIT_PURCHASE_KEYS = ("credit_purchase_user_id", "credit_purchase_payment_id", "credit_purchase_quantity")
_SHARED_CHECKOUT_KEYS = ("checkout_amount", "checkout_description")

_ALL_CHECKOUT_KEYS: tuple[str, ...] = _MEMBERSHIP_RENEWAL_KEYS + _CREDIT_PURCHASE_KEYS + _SHARED_CHECKOUT_KEYS


def get_user_id_from_session(request: Request, user: User | None) -> int | None:
    return request.session.get("membership_renewal_user_id") or request.session.get("credit_purchase_user_id") or (user.id if user is not None else None)


def clear_session_keys(request: Request, *keys: str) -> None:
    for key in keys:
        request.session.pop(key, None)


def _clear_all_checkout_keys(session: MutableMapping[str, Any]) -> None:
    for key in _ALL_CHECKOUT_KEYS:
        session.pop(key, None)


def set_membership_renewal_checkout(session: MutableMapping[str, Any], data: dict[str, Any]) -> None:
    _clear_all_checkout_keys(session)
    session["membership_renewal_user_id"] = data["user_id"]
    session["membership_renewal_payment_id"] = data["payment_id"]
    session["checkout_amount"] = data["amount"]
    session["checkout_description"] = data["description"]


def set_credit_purchase_checkout(session: MutableMapping[str, Any], data: dict[str, Any]) -> None:
    _clear_all_checkout_keys(session)
    session["credit_purchase_user_id"] = data["user_id"]
    session["credit_purchase_payment_id"] = data["payment_id"]
    session["credit_purchase_quantity"] = data["quantity"]
    session["checkout_amount"] = data["amount"]
    session["checkout_description"] = data["description"]
