from datetime import date, timedelta

import pytest


def test_is_active(test_user):
    assert test_user.membership.is_active()


def test_credits_remaining(test_user):
    """Test credits remaining returns sum of initial and purchased credits"""
    assert test_user.membership.credits_remaining() == test_user.membership.initial_credits + test_user.membership.purchased_credits


def test_credits_remaining_shows_negative(test_user):
    """Test that credits_remaining shows negative values"""
    test_user.membership.initial_credits = -5
    test_user.membership.purchased_credits = 0
    assert test_user.membership.credits_remaining() == -5


@pytest.mark.parametrize(
    "initial,purchased,allow_negative,expected_result",
    [
        (2, 5, False, True),
        (0, 5, False, True),
        (0, 0, False, False),
        (None, 3, False, True),
        (0, None, False, False),  # None is treated as 0, no credits available
        (None, None, False, False),
        (0, 0, True, True),
        (None, None, True, True),
    ],
)
def test_use_credit_success_and_failure(test_user, initial, purchased, allow_negative, expected_result):
    """Test use_credit success/failure with various credit states."""
    m = test_user.membership
    m.initial_credits = initial
    m.purchased_credits = purchased

    result = m.use_credit(allow_negative=allow_negative)

    assert result is expected_result


@pytest.mark.parametrize(
    "initial,purchased,allow_negative,expected_initial,expected_purchased",
    [
        (2, 5, False, 1, 5),
        (0, 5, False, 0, 4),
        (0, 0, True, -1, 0),
        (0, 0, False, 0, 0),
    ],
)
def test_use_credit_deducts_correct_source(test_user, initial, purchased, allow_negative, expected_initial, expected_purchased):
    """Test that credits are deducted from the correct source (initial first, then purchased)."""
    m = test_user.membership
    m.initial_credits = initial
    m.purchased_credits = purchased

    m.use_credit(allow_negative=allow_negative)

    assert m.initial_credits == expected_initial
    assert m.purchased_credits == expected_purchased


def test_use_credit_falls_through_to_purchased(test_user):
    """Test that use_credit falls through to purchased credits when initial is exhausted."""
    m = test_user.membership
    m.initial_credits = 1
    m.purchased_credits = 2

    m.use_credit()
    assert m.initial_credits == 0
    assert m.purchased_credits == 2

    m.use_credit()
    assert m.initial_credits == 0
    assert m.purchased_credits == 1


@pytest.mark.parametrize(
    "initial,purchased,allow_negative,expected_initial",
    [
        (0, 0, True, -2),
        (-3, 0, True, -5),
    ],
)
def test_use_credit_negative_balance(test_user, initial, purchased, allow_negative, expected_initial):
    """Test that allow_negative allows going into negative balance."""
    m = test_user.membership
    m.initial_credits = initial
    m.purchased_credits = purchased

    m.use_credit(allow_negative=allow_negative)
    m.use_credit(allow_negative=allow_negative)

    assert m.initial_credits == expected_initial
    assert m.purchased_credits == 0


def test_use_credit_with_allow_negative_inactive_membership(test_user):
    """Test that allow_negative only works for active memberships."""
    test_user.membership.initial_credits = 0
    test_user.membership.purchased_credits = 0
    test_user.membership.status = "pending"
    result = test_user.membership.use_credit(allow_negative=True)

    assert result is False


@pytest.mark.parametrize(
    "initial,purchased,status,expiry_date,allow_negative,expected_result",
    [
        (0, 0, "pending", date.today() + timedelta(days=30), True, False),
        (0, 0, "active", date.today() - timedelta(days=1), True, False),
        (0, 0, "active", date.today(), True, True),
        (5, 0, "pending", date.today() + timedelta(days=30), False, True),
    ],
)
def test_use_credit_membership_status(test_user, initial, purchased, status, expiry_date, allow_negative, expected_result):
    """Test use_credit behavior based on membership status."""
    m = test_user.membership
    m.initial_credits = initial
    m.purchased_credits = purchased
    m.status = status
    m.expiry_date = expiry_date

    result = m.use_credit(allow_negative=allow_negative)

    assert result is expected_result


def test_add_credits(test_user):
    """Test adding credits - should add to purchased credits"""
    initial_purchased = test_user.membership.purchased_credits
    test_user.membership.add_credits(5)

    assert test_user.membership.purchased_credits == initial_purchased + 5


def test_add_credits_then_use(test_user):
    """Test that add_credits allows use_credit to succeed."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    m.add_credits(3)
    result = m.use_credit()

    assert result is True
    assert m.purchased_credits == 2


def test_use_credit_then_add_credits_restores_availability(test_user):
    """Test that credits can be added after being exhausted."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    assert m.use_credit() is False

    m.add_credits(1)
    assert m.use_credit() is True
    assert m.purchased_credits == 0


def test_negative_balance_then_add_credits(test_user):
    """After going negative via allow_negative, adding credits doesn't auto-clear the debt."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    m.use_credit(allow_negative=True)
    m.add_credits(5)

    result = m.use_credit()
    assert result is True
    assert m.purchased_credits == 4
    assert m.initial_credits == -1


def test_renew(test_user):
    """Test membership renewal - resets initial credits, keeps purchased"""
    test_user.membership.initial_credits = 5
    test_user.membership.purchased_credits = 10
    expiry = date.today() + timedelta(days=365)
    test_user.membership.renew(expiry_date=expiry)

    assert test_user.membership.start_date == date.today()
    assert test_user.membership.expiry_date == expiry
    assert test_user.membership.initial_credits == 20
    assert test_user.membership.purchased_credits == 10
    assert test_user.membership.status == "active"


def test_renew_with_custom_credits(test_user):
    """Test membership renewal with custom initial credits amount"""
    test_user.membership.purchased_credits = 10
    expiry = date.today() + timedelta(days=365)
    test_user.membership.renew(expiry_date=expiry, initial_credits=25)

    assert test_user.membership.initial_credits == 25
    assert test_user.membership.purchased_credits == 10


def test_expire_initial_credits(test_user):
    """Test expiring initial credits while retaining purchased"""
    test_user.membership.initial_credits = 15
    test_user.membership.purchased_credits = 8
    test_user.membership.expire_initial_credits()

    assert test_user.membership.initial_credits == 0
    assert test_user.membership.purchased_credits == 8


def test_activate(test_user):
    """Test activating a pending membership"""
    test_user.membership.status = "pending"
    test_user.membership.activate()

    assert test_user.membership.status == "active"


def test_membership_repr(test_user):
    """Test membership string representation"""
    repr_str = repr(test_user.membership)

    assert "Membership" in repr_str
    assert str(test_user.id) in repr_str
