from app import db
from app.models import Payment
from app.repositories import PaymentRepository


def test_payment_repository_get_by_id(app, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    found = PaymentRepository.get_by_id(payment.id)
    assert found is not None
    assert found.user_id == test_user.id


def test_payment_repository_get_pending_cash(app, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    pending = PaymentRepository.get_pending_cash()
    assert len(pending) >= 1


def test_payment_repository_count_pending_cash(app, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=5000,
        currency="EUR",
        payment_type="credits",
        payment_method="cash",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    count = PaymentRepository.count_pending_cash()
    assert count >= 1


def test_payment_repository_get_by_user(app, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    payments = PaymentRepository.get_by_user(test_user.id)
    assert len(payments) >= 1
