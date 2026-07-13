from app import db
from app.services import finance, settings
from tests.helpers import create_payment_for_user


def test_record_sumup_payment_transactions_is_idempotent(app, test_user):
    settings.set("sumup_fee_percentage", "2.5")
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="membership",
        status="completed",
        external_transaction_id="sumup-txn-123",
        payment_processor="sumup",
    )

    first = finance.record_sumup_payment_transactions(
        payment_amount_cents=payment.amount_cents,
        payment_type="membership",
        description="Membership payment",
        created_by_id=test_user.id,
        receipt_reference=payment.external_transaction_id,
    )
    second = finance.record_sumup_payment_transactions(
        payment_amount_cents=payment.amount_cents,
        payment_type="membership",
        description="Membership payment",
        created_by_id=test_user.id,
        receipt_reference=payment.external_transaction_id,
    )

    assert first.success is True
    assert second.success is True
    assert "already recorded" in second.message


def test_record_cash_payment_transactions_is_idempotent(app, test_user):
    payment = create_payment_for_user(
        db,
        test_user,
        payment_type="membership",
        status="completed",
        payment_processor="cash",
    )

    first = finance.record_cash_payment_transaction(
        payment_amount_cents=payment.amount_cents,
        payment_type="membership",
        description="Cash membership payment",
        created_by_id=test_user.id,
        payment_id=payment.id,
    )
    second = finance.record_cash_payment_transaction(
        payment_amount_cents=payment.amount_cents,
        payment_type="membership",
        description="Cash membership payment",
        created_by_id=test_user.id,
        payment_id=payment.id,
    )

    assert first.success is True
    assert second.success is True
    assert "already recorded" in second.message
