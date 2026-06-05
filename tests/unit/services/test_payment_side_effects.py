from unittest.mock import patch

from app import db
from app.models import FinancialTransaction
from app.services.payment_side_effects import emit_payment_side_effects, replay_payment_side_effects
from tests.helpers import create_payment_for_user


def test_emit_payment_side_effects_skips_when_already_completed(app, test_user):
    from app.events import payment_completed

    received: list[dict] = []
    payment = create_payment_for_user(db, test_user, status="completed", payment_type="membership")

    with payment_completed.connected_to(lambda sender, **kw: received.append(kw)):
        emit_payment_side_effects(payment, test_user, already_completed=True)

    assert received == []


def test_replay_payment_side_effects_records_ledger(app, test_user, fake_mailer):
    payment = create_payment_for_user(
        db,
        test_user,
        status="completed",
        payment_type="membership",
        payment_method="cash",
        payment_processor="cash",
    )

    result = replay_payment_side_effects(payment.id)

    assert result.success is True
    txns = FinancialTransaction.query.filter_by(category="membership_fees", type="income").all()
    assert len(txns) == 1
    assert len(fake_mailer.sent_messages) == 1


def test_replay_payment_side_effects_is_idempotent(app, test_user, fake_mailer):
    payment = create_payment_for_user(
        db,
        test_user,
        status="completed",
        payment_type="membership",
        payment_processor="cash",
    )

    first = replay_payment_side_effects(payment.id)
    second = replay_payment_side_effects(payment.id)

    assert first.success is True
    assert second.success is True
    assert FinancialTransaction.query.filter_by(category="membership_fees").count() == 1


def test_replay_payment_side_effects_rejects_pending(app, test_user):
    payment = create_payment_for_user(db, test_user, status="pending", payment_method="cash")

    result = replay_payment_side_effects(payment.id)

    assert result.success is False
    assert "completed" in result.message.lower()


def test_replay_payment_side_effects_credit_receipt(app, test_user, fake_mailer):
    payment = create_payment_for_user(
        db,
        test_user,
        status="completed",
        payment_type="credits",
        payment_method="cash",
        payment_processor="cash",
        description="3 shooting credits",
    )

    result = replay_payment_side_effects(payment.id)

    assert result.success is True
    assert len(fake_mailer.sent_messages) == 1


@patch("app.services.mail.send_payment_receipt", side_effect=RuntimeError("smtp down"))
def test_replay_payment_side_effects_mail_failure(mock_mail, app, test_user):
    payment = create_payment_for_user(db, test_user, status="completed", payment_type="membership")

    result = replay_payment_side_effects(payment.id)

    assert result.success is False
    assert "receipt email" in result.message.lower()
