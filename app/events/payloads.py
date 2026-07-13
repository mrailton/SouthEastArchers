"""Typed payloads for domain event signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.events import (
    cash_payment_submitted,
    credit_purchased,
    membership_activated,
    password_reset_requested,
    payment_completed,
    user_activated,
    user_registered,
)


@dataclass(frozen=True, slots=True)
class UserIdPayload:
    user_id: int

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, Any]) -> UserIdPayload:
        return cls(user_id=int(kwargs["user_id"]))


@dataclass(frozen=True, slots=True)
class PasswordResetPayload:
    user_id: int
    token: str

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, Any]) -> PasswordResetPayload:
        return cls(user_id=int(kwargs["user_id"]), token=str(kwargs["token"]))


@dataclass(frozen=True, slots=True)
class PaymentCompletedPayload:
    user_id: int
    payment_id: int
    payment_type: str

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, Any]) -> PaymentCompletedPayload:
        return cls(
            user_id=int(kwargs["user_id"]),
            payment_id=int(kwargs["payment_id"]),
            payment_type=str(kwargs["payment_type"]),
        )


@dataclass(frozen=True, slots=True)
class CreditPurchasedPayload:
    user_id: int
    payment_id: int
    quantity: int

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, Any]) -> CreditPurchasedPayload:
        return cls(
            user_id=int(kwargs["user_id"]),
            payment_id=int(kwargs["payment_id"]),
            quantity=int(kwargs["quantity"]),
        )


@dataclass(frozen=True, slots=True)
class CashPaymentSubmittedPayload:
    user_id: int
    payment_id: int

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, Any]) -> CashPaymentSubmittedPayload:
        return cls(user_id=int(kwargs["user_id"]), payment_id=int(kwargs["payment_id"]))


@dataclass(frozen=True, slots=True)
class MembershipActivatedPayload:
    user_id: int
    payment_id: int | None = None

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, Any]) -> MembershipActivatedPayload:
        raw_payment_id = kwargs.get("payment_id")
        payment_id = int(raw_payment_id) if raw_payment_id is not None else None
        return cls(user_id=int(kwargs["user_id"]), payment_id=payment_id)


def emit_user_registered(user_id: int) -> None:
    user_registered.send(**asdict(UserIdPayload(user_id=user_id)))


def emit_user_activated(user_id: int) -> None:
    user_activated.send(**asdict(UserIdPayload(user_id=user_id)))


def emit_password_reset_requested(user_id: int, token: str) -> None:
    password_reset_requested.send(**asdict(PasswordResetPayload(user_id=user_id, token=token)))


def emit_payment_completed(user_id: int, payment_id: int, payment_type: str) -> None:
    payment_completed.send(**asdict(PaymentCompletedPayload(user_id=user_id, payment_id=payment_id, payment_type=payment_type)))


def emit_credit_purchased(user_id: int, payment_id: int, quantity: int) -> None:
    credit_purchased.send(**asdict(CreditPurchasedPayload(user_id=user_id, payment_id=payment_id, quantity=quantity)))


def emit_cash_payment_submitted(user_id: int, payment_id: int) -> None:
    cash_payment_submitted.send(**asdict(CashPaymentSubmittedPayload(user_id=user_id, payment_id=payment_id)))


def emit_membership_activated(user_id: int, payment_id: int | None = None) -> None:
    membership_activated.send(**asdict(MembershipActivatedPayload(user_id=user_id, payment_id=payment_id)))
