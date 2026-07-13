import pytest

from app.events import payment_completed
from app.events.payloads import (
    CashPaymentSubmittedPayload,
    CreditPurchasedPayload,
    PaymentCompletedPayload,
    emit_payment_completed,
)


def test_payment_completed_payload_from_kwargs():
    payload = PaymentCompletedPayload.from_kwargs(
        {"user_id": 1, "payment_id": 42, "payment_type": "membership"},
    )
    assert payload.user_id == 1
    assert payload.payment_id == 42
    assert payload.payment_type == "membership"


def test_emit_payment_completed_delivers_contract_kwargs():
    received: list[dict] = []

    with payment_completed.connected_to(lambda sender, **kw: received.append(kw)):
        emit_payment_completed(7, 99, "credits")

    assert received == [{"user_id": 7, "payment_id": 99, "payment_type": "credits"}]


def test_credit_purchased_payload_requires_quantity():
    with pytest.raises(KeyError):
        CreditPurchasedPayload.from_kwargs({"user_id": 1, "payment_id": 2})


def test_cash_payment_submitted_payload_from_kwargs():
    payload = CashPaymentSubmittedPayload.from_kwargs({"user_id": 3, "payment_id": 8})
    assert payload.user_id == 3
    assert payload.payment_id == 8
