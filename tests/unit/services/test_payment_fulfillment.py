from app import db
from app.models import Credit
from app.services import payment_fulfillment, payment_processing
from tests.helpers import create_payment_for_user


def test_fulfill_payment_is_idempotent(app, test_user):
    payment = create_payment_for_user(db, test_user, payment_type="membership", status="pending")
    first = payment_fulfillment.fulfill_payment(
        payment,
        test_user,
        processor="sumup",
        transaction_id="txn_once",
        membership_mode="activate_only",
    )
    assert first.success is True
    assert first.data is not None
    assert first.data.already_completed is False

    second = payment_fulfillment.fulfill_payment(
        payment,
        test_user,
        processor="sumup",
        transaction_id="txn_once",
        membership_mode="activate_only",
    )
    assert second.success is True
    assert second.data is not None
    assert second.data.already_completed is True


def test_handle_signup_payment_twice_does_not_duplicate_events(app, test_user, mocker):
    payment = create_payment_for_user(db, test_user, payment_type="membership", status="pending")
    send = mocker.patch("app.services.payment_side_effects.payment_completed.send")

    payment_processing.handle_signup_payment(test_user.id, payment.id, "txn_dup")
    payment_processing.handle_signup_payment(test_user.id, payment.id, "txn_dup")

    assert send.call_count == 1


def test_credit_fulfillment_adds_single_credit_row(app, test_user):
    payment = create_payment_for_user(db, test_user, payment_type="credits", status="pending")
    payment_fulfillment.fulfill_payment(payment, test_user, processor="sumup", transaction_id="txn_c", quantity=3)
    payment_fulfillment.fulfill_payment(payment, test_user, processor="sumup", transaction_id="txn_c", quantity=3)

    credits = db.session.query(Credit).filter_by(payment_id=payment.id).all()
    assert len(credits) == 1
    assert credits[0].amount == 3
