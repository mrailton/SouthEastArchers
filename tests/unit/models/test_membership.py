from datetime import date, timedelta


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
    expiry = date.today() + timedelta(days=365)
    test_user.membership.renew(expiry_date=expiry)

    assert test_user.membership.start_date == date.today()
    assert test_user.membership.expiry_date == expiry
    assert test_user.membership.initial_credits == 20
    assert test_user.membership.purchased_credits == 10  # Purchased credits retained
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


# ---------------------------------------------------------------------------
# use_credit — edge cases and complex logic
# ---------------------------------------------------------------------------


def test_uses_initial_before_purchased(test_user):
    m = test_user.membership
    m.initial_credits = 3
    m.purchased_credits = 5

    m.use_credit()

    assert m.initial_credits == 2
    assert m.purchased_credits == 5


def test_falls_through_to_purchased_when_initial_exhausted(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 4

    result = m.use_credit()

    assert result is True
    assert m.initial_credits == 0
    assert m.purchased_credits == 3


def test_boundary_transition_initial_to_purchased(test_user):
    """Last initial credit used, then next call takes from purchased."""
    m = test_user.membership
    m.initial_credits = 1
    m.purchased_credits = 2

    # This should take the last initial credit
    m.use_credit()
    assert m.initial_credits == 0
    assert m.purchased_credits == 2

    # This should take from purchased
    m.use_credit()
    assert m.initial_credits == 0
    assert m.purchased_credits == 1


def test_full_depletion_sequence(test_user):
    """Deplete initial, then purchased, then refuse without allow_negative."""
    m = test_user.membership
    m.initial_credits = 1
    m.purchased_credits = 1

    assert m.use_credit() is True  # initial 1→0
    assert m.use_credit() is True  # purchased 1→0
    assert m.use_credit() is False  # nothing left

    assert m.initial_credits == 0
    assert m.purchased_credits == 0


def test_none_initial_credits_treated_as_zero(test_user):
    m = test_user.membership
    m.initial_credits = None
    m.purchased_credits = 3

    result = m.use_credit()

    assert result is True
    assert m.purchased_credits == 2


def test_none_purchased_credits_treated_as_zero(test_user):
    m = test_user.membership
    m.initial_credits = 2
    m.purchased_credits = None

    result = m.use_credit()

    assert result is True
    assert m.initial_credits == 1


def test_both_none_no_credits_available(test_user):
    m = test_user.membership
    m.initial_credits = None
    m.purchased_credits = None

    result = m.use_credit()

    assert result is False


def test_both_none_with_allow_negative(test_user):
    m = test_user.membership
    m.initial_credits = None
    m.purchased_credits = None

    result = m.use_credit(allow_negative=True)

    assert result is True
    assert m.initial_credits == -1


def test_negative_deducts_from_initial_not_purchased(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    m.use_credit(allow_negative=True)

    assert m.initial_credits == -1
    assert m.purchased_credits == 0


def test_successive_negative_deductions(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    for i in range(1, 6):
        assert m.use_credit(allow_negative=True) is True
        assert m.initial_credits == -i

    assert m.purchased_credits == 0


def test_already_negative_keeps_decrementing(test_user):
    m = test_user.membership
    m.initial_credits = -3
    m.purchased_credits = 0

    result = m.use_credit(allow_negative=True)

    assert result is True
    assert m.initial_credits == -4


def test_positive_total_uses_normal_path_even_with_allow_negative(test_user):
    """When credits are available, allow_negative has no effect on the deduction path."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 5

    result = m.use_credit(allow_negative=True)

    # Total > 0, so normal path: purchased decremented, not initial
    assert result is True
    assert m.initial_credits == 0
    assert m.purchased_credits == 4


def test_allow_negative_with_initial_remaining(test_user):
    """allow_negative flag is irrelevant when initial credits are positive."""
    m = test_user.membership
    m.initial_credits = 3
    m.purchased_credits = 0

    result = m.use_credit(allow_negative=True)

    assert result is True
    assert m.initial_credits == 2
    assert m.purchased_credits == 0


def test_default_allow_negative_is_false(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    result = m.use_credit()

    assert result is False
    assert m.initial_credits == 0
    assert m.purchased_credits == 0


def test_allow_negative_refused_for_pending_membership(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0
    m.status = "pending"

    result = m.use_credit(allow_negative=True)

    assert result is False
    assert m.initial_credits == 0


def test_allow_negative_refused_for_expired_by_date(test_user):
    """Membership is 'active' status but expiry_date is in the past."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0
    m.status = "active"
    m.expiry_date = date.today() - timedelta(days=1)

    result = m.use_credit(allow_negative=True)

    assert result is False
    assert m.initial_credits == 0


def test_allow_negative_accepted_on_expiry_day(test_user):
    """Membership expiring today is still considered active."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0
    m.status = "active"
    m.expiry_date = date.today()

    result = m.use_credit(allow_negative=True)

    assert result is True
    assert m.initial_credits == -1


def test_inactive_membership_can_still_use_positive_credits(test_user):
    """Positive credits can be used regardless of membership status."""
    m = test_user.membership
    m.initial_credits = 5
    m.purchased_credits = 0
    m.status = "pending"

    result = m.use_credit()

    assert result is True
    assert m.initial_credits == 4


def test_expired_by_date_can_still_use_positive_credits(test_user):
    """Positive credits usable even if membership has expired by date."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 3
    m.status = "active"
    m.expiry_date = date.today() - timedelta(days=30)

    result = m.use_credit()

    assert result is True
    assert m.purchased_credits == 2


def test_add_credits_then_use(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    m.add_credits(3)
    result = m.use_credit()

    assert result is True
    # Purchased credits added, but initial is 0 so deduct from purchased
    assert m.initial_credits == 0
    assert m.purchased_credits == 2


def test_use_credit_then_add_credits_restores_availability(test_user):
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    assert m.use_credit() is False

    m.add_credits(1)
    assert m.use_credit() is True
    assert m.purchased_credits == 0


def test_negative_balance_then_add_credits_covers_debt(test_user):
    """After going negative via allow_negative, adding credits doesn't auto-clear the debt
    but the total becomes positive and normal path is used."""
    m = test_user.membership
    m.initial_credits = 0
    m.purchased_credits = 0

    m.use_credit(allow_negative=True)  # initial → -1
    m.add_credits(5)  # purchased → 5

    # Total = -1 + 5 = 4 > 0, so use_credit should succeed via normal path
    result = m.use_credit()
    assert result is True
    # initial is -1 (not > 0), so purchased is decremented
    assert m.purchased_credits == 4
    assert m.initial_credits == -1
