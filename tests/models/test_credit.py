"""Tests for credit model"""

from datetime import date

import pytest

from app.models import Credit, User


def test_create_credit(app):
    """Test creating a basic credit"""
    from app import db

    user = User(name="Test User", email="test@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    credit = Credit(user_id=user.id, amount=10)
    db.session.add(credit)
    db.session.commit()

    assert credit.id is not None
    assert credit.amount == 10
    assert credit.user_id == user.id
    assert credit.created_at is not None


def test_create_credit_default_amount(app):
    """Test credit has default amount of 1"""
    from app import db

    user = User(name="Test User", email="test2@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    credit = Credit(user_id=user.id)
    db.session.add(credit)
    db.session.commit()

    assert credit.amount == 1


def test_credit_with_payment(app):
    """Test credit linked to payment"""
    from app import db
    from app.models import Payment

    user = User(name="Test User", email="test3@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    payment = Payment(
        user_id=user.id,
        amount_cents=2500,  # Store directly in cents
        currency="EUR",
        payment_type="credits",
        status="completed",
    )
    db.session.add(payment)
    db.session.flush()

    credit = Credit(user_id=user.id, amount=5, payment_id=payment.id)
    db.session.add(credit)
    db.session.commit()

    assert credit.payment_id == payment.id
    assert credit.amount == 5


def test_credit_without_payment(app):
    """Test credit can be created without payment (e.g., admin grant)"""
    from app import db

    user = User(name="Test User", email="test4@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    credit = Credit(user_id=user.id, amount=3, payment_id=None)
    db.session.add(credit)
    db.session.commit()

    assert credit.payment_id is None
    assert credit.amount == 3


def test_credit_relationship_with_user(app):
    """Test credit relationship with user"""
    from app import db

    user = User(name="Test User", email="test5@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    credit = Credit(user_id=user.id, amount=7)
    db.session.add(credit)
    db.session.commit()

    assert credit.user == user
    assert credit in user.credits


def test_credit_repr(app):
    """Test credit string representation"""
    from app import db

    user = User(name="Test User", email="test6@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    credit = Credit(user_id=user.id, amount=15)
    db.session.add(credit)
    db.session.commit()

    repr_str = repr(credit)
    assert "Credit" in repr_str
    assert str(user.id) in repr_str
    assert "15" in repr_str
