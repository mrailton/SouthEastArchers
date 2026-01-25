"""Tests for membership model"""

from datetime import date


def test_is_active(test_user):
    assert test_user.membership.is_active()


def test_credits_remaining(test_user):
    """Test credits remaining returns sum of initial and purchased credits"""
    assert test_user.membership.credits_remaining() == test_user.membership.initial_credits + test_user.membership.purchased_credits


def test_use_credit(test_user):
    """Test using a credit - should use initial credits first"""
    initial_credits = test_user.membership.initial_credits
    result = test_user.membership.use_credit()

    assert result is True
    assert test_user.membership.initial_credits == initial_credits - 1


def test_use_credit_when_none_left(test_user):
    """Test using credit when none left (without allow_negative)"""
    test_user.membership.initial_credits = 0
    test_user.membership.purchased_credits = 0
    result = test_user.membership.use_credit()

    assert result is False
    assert test_user.membership.initial_credits == 0
    assert test_user.membership.purchased_credits == 0


def test_use_credit_with_allow_negative(test_user):
    """Test using credit with allow_negative allows going into negative"""
    test_user.membership.initial_credits = 0
    test_user.membership.purchased_credits = 0
    result = test_user.membership.use_credit(allow_negative=True)

    assert result is True
    assert test_user.membership.initial_credits == -1


def test_use_credit_with_allow_negative_inactive_membership(test_user):
    """Test that allow_negative only works for active memberships"""
    test_user.membership.initial_credits = 0
    test_user.membership.purchased_credits = 0
    test_user.membership.status = "pending"  # Make it inactive
    result = test_user.membership.use_credit(allow_negative=True)

    assert result is False
    assert test_user.membership.initial_credits == 0


def test_use_credit_multiple_negative(test_user):
    """Test using multiple credits with negative balance"""
    test_user.membership.initial_credits = 0
    test_user.membership.purchased_credits = 0

    # Use first credit
    result1 = test_user.membership.use_credit(allow_negative=True)
    assert result1 is True
    assert test_user.membership.initial_credits == -1

    # Use second credit (already negative)
    result2 = test_user.membership.use_credit(allow_negative=True)
    assert result2 is True
    assert test_user.membership.initial_credits == -2


def test_use_credit_uses_initial_first_then_purchased(test_user):
    """Test that credits are used in correct order: initial first, then purchased"""
    test_user.membership.initial_credits = 2
    test_user.membership.purchased_credits = 5

    # Use first credit - should come from initial
    test_user.membership.use_credit()
    assert test_user.membership.initial_credits == 1
    assert test_user.membership.purchased_credits == 5

    # Use second credit - should come from initial
    test_user.membership.use_credit()
    assert test_user.membership.initial_credits == 0
    assert test_user.membership.purchased_credits == 5

    # Use third credit - should come from purchased
    test_user.membership.use_credit()
    assert test_user.membership.initial_credits == 0
    assert test_user.membership.purchased_credits == 4


def test_add_credits(test_user):
    """Test adding credits - should add to purchased credits"""
    initial_purchased = test_user.membership.purchased_credits
    test_user.membership.add_credits(5)

    assert test_user.membership.purchased_credits == initial_purchased + 5


def test_credits_remaining_shows_negative(test_user):
    """Test that credits_remaining shows negative values"""
    test_user.membership.initial_credits = -5
    test_user.membership.purchased_credits = 0
    assert test_user.membership.credits_remaining() == -5


def test_renew(test_user):
    """Test membership renewal - resets initial credits, keeps purchased"""
    test_user.membership.initial_credits = 5
    test_user.membership.purchased_credits = 10
    test_user.membership.renew()

    assert test_user.membership.start_date == date.today()
    assert test_user.membership.initial_credits == 20
    assert test_user.membership.purchased_credits == 10  # Purchased credits retained
    assert test_user.membership.status == "active"


def test_renew_with_custom_credits(test_user):
    """Test membership renewal with custom initial credits amount"""
    test_user.membership.purchased_credits = 10
    test_user.membership.renew(initial_credits=25)

    assert test_user.membership.initial_credits == 25
    assert test_user.membership.purchased_credits == 10


def test_expire_initial_credits(test_user):
    """Test expiring initial credits while retaining purchased"""
    test_user.membership.initial_credits = 15
    test_user.membership.purchased_credits = 8
    test_user.membership.expire_initial_credits()

    assert test_user.membership.initial_credits == 0
    assert test_user.membership.purchased_credits == 8  # Purchased retained


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
