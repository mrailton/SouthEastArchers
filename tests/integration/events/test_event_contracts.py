"""Tests that verify domain event signals fire with the correct kwargs.

These tests assert the *contract* between services (emitters) and handlers
(subscribers) without testing the handler side effects.  Each test temporarily
subscribes a recording callback via ``signal.connected_to()`` and checks the
kwargs that were delivered.
"""

from app import db
from app.enums import PaymentType
from app.events import cash_payment_submitted, credit_purchased, payment_completed
from app.services import PaymentProcessingService, PaymentService
from tests.helpers import create_payment_for_user

# ---------------------------------------------------------------------------
# payment_completed signal
# ---------------------------------------------------------------------------


def test_signup_emits_payment_completed_with_correct_kwargs(app, test_user, fake_mailer):
    """handle_signup_payment emits payment_completed with user_id, payment_id, payment_type."""
    test_user.membership.status = "pending"
    db.session.commit()
    payment = create_payment_for_user(db, test_user, status="pending")

    received: list[dict] = []

    with payment_completed.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentProcessingService.handle_signup_payment(test_user.id, payment.id, "txn_contract_1")

    assert len(received) == 1
    assert received[0]["user_id"] == test_user.id
    assert received[0]["payment_id"] == payment.id
    assert received[0]["payment_type"] == PaymentType.MEMBERSHIP


def test_membership_renewal_emits_payment_completed(app, test_user, fake_mailer):
    """handle_membership_renewal emits payment_completed with correct kwargs."""
    payment = create_payment_for_user(db, test_user, status="pending")

    received: list[dict] = []

    with payment_completed.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentProcessingService.handle_membership_renewal(test_user.id, payment.id, "txn_contract_2")

    assert len(received) == 1
    assert received[0]["user_id"] == test_user.id
    assert received[0]["payment_id"] == payment.id
    assert received[0]["payment_type"] == PaymentType.MEMBERSHIP


# ---------------------------------------------------------------------------
# credit_purchased signal
# ---------------------------------------------------------------------------


def test_credit_purchase_emits_credit_purchased_with_correct_kwargs(app, test_user, fake_mailer):
    """handle_credit_purchase emits credit_purchased with user_id, payment_id, quantity."""
    payment = create_payment_for_user(db, test_user, payment_type="credits", status="pending")
    quantity = 7

    received: list[dict] = []

    with credit_purchased.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentProcessingService.handle_credit_purchase(test_user.id, payment.id, quantity, "txn_contract_3")

    assert len(received) == 1
    assert received[0]["user_id"] == test_user.id
    assert received[0]["payment_id"] == payment.id
    assert received[0]["quantity"] == quantity


# ---------------------------------------------------------------------------
# cash_payment_submitted signal
# ---------------------------------------------------------------------------


def test_cash_membership_emits_cash_payment_submitted(app, test_user, fake_mailer):
    """initiate_cash_membership_payment emits cash_payment_submitted with user_id, payment_id."""
    received: list[dict] = []

    with cash_payment_submitted.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentService.initiate_cash_membership_payment(test_user)

    assert len(received) == 1
    assert received[0]["user_id"] == test_user.id
    assert "payment_id" in received[0]
    assert isinstance(received[0]["payment_id"], int)


def test_cash_credit_purchase_emits_cash_payment_submitted(app, test_user, fake_mailer):
    """initiate_cash_credit_purchase emits cash_payment_submitted with user_id, payment_id."""
    received: list[dict] = []

    with cash_payment_submitted.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentService.initiate_cash_credit_purchase(test_user, quantity=3)

    assert len(received) == 1
    assert received[0]["user_id"] == test_user.id
    assert "payment_id" in received[0]
    assert isinstance(received[0]["payment_id"], int)


# ---------------------------------------------------------------------------
# Negative cases — signals should NOT fire on failure
# ---------------------------------------------------------------------------


def test_signup_does_not_emit_when_user_not_found(app, test_user, fake_mailer):
    """payment_completed should not fire if user lookup fails."""
    payment = create_payment_for_user(db, test_user, status="pending")

    received: list[dict] = []

    with payment_completed.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentProcessingService.handle_signup_payment(user_id=99999, payment_id=payment.id, transaction_id="txn_nope")

    assert len(received) == 0


def test_credit_purchase_does_not_emit_when_payment_not_found(app, fake_mailer):
    """credit_purchased should not fire if payment lookup fails."""
    received: list[dict] = []

    with credit_purchased.connected_to(lambda sender, **kw: received.append(kw)):
        PaymentProcessingService.handle_credit_purchase(user_id=1, payment_id=99999, quantity=5, transaction_id="txn_nope")

    assert len(received) == 0
