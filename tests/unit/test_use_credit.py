"""Unit tests for Membership.use_credit() — edge cases and complex logic."""

from datetime import date, timedelta


class TestUseCreditPriorityDeduction:
    """Verify initial credits are always consumed before purchased credits."""

    def test_uses_initial_before_purchased(self, test_user):
        m = test_user.membership
        m.initial_credits = 3
        m.purchased_credits = 5

        m.use_credit()

        assert m.initial_credits == 2
        assert m.purchased_credits == 5

    def test_falls_through_to_purchased_when_initial_exhausted(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 4

        result = m.use_credit()

        assert result is True
        assert m.initial_credits == 0
        assert m.purchased_credits == 3

    def test_boundary_transition_initial_to_purchased(self, test_user):
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

    def test_full_depletion_sequence(self, test_user):
        """Deplete initial, then purchased, then refuse without allow_negative."""
        m = test_user.membership
        m.initial_credits = 1
        m.purchased_credits = 1

        assert m.use_credit() is True  # initial 1→0
        assert m.use_credit() is True  # purchased 1→0
        assert m.use_credit() is False  # nothing left

        assert m.initial_credits == 0
        assert m.purchased_credits == 0


class TestUseCreditNoneFieldHandling:
    """Ensure None values for credit fields are treated as zero."""

    def test_none_initial_credits_treated_as_zero(self, test_user):
        m = test_user.membership
        m.initial_credits = None
        m.purchased_credits = 3

        result = m.use_credit()

        assert result is True
        assert m.purchased_credits == 2

    def test_none_purchased_credits_treated_as_zero(self, test_user):
        m = test_user.membership
        m.initial_credits = 2
        m.purchased_credits = None

        result = m.use_credit()

        assert result is True
        assert m.initial_credits == 1

    def test_both_none_no_credits_available(self, test_user):
        m = test_user.membership
        m.initial_credits = None
        m.purchased_credits = None

        result = m.use_credit()

        assert result is False

    def test_both_none_with_allow_negative(self, test_user):
        m = test_user.membership
        m.initial_credits = None
        m.purchased_credits = None

        result = m.use_credit(allow_negative=True)

        assert result is True
        assert m.initial_credits == -1


class TestUseCreditAllowNegative:
    """Test the allow_negative override for admin bookings."""

    def test_negative_deducts_from_initial_not_purchased(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0

        m.use_credit(allow_negative=True)

        assert m.initial_credits == -1
        assert m.purchased_credits == 0

    def test_successive_negative_deductions(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0

        for i in range(1, 6):
            assert m.use_credit(allow_negative=True) is True
            assert m.initial_credits == -i

        assert m.purchased_credits == 0

    def test_already_negative_keeps_decrementing(self, test_user):
        m = test_user.membership
        m.initial_credits = -3
        m.purchased_credits = 0

        result = m.use_credit(allow_negative=True)

        assert result is True
        assert m.initial_credits == -4

    def test_positive_total_uses_normal_path_even_with_allow_negative(self, test_user):
        """When credits are available, allow_negative has no effect on the deduction path."""
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 5

        result = m.use_credit(allow_negative=True)

        # Total > 0, so normal path: purchased decremented, not initial
        assert result is True
        assert m.initial_credits == 0
        assert m.purchased_credits == 4

    def test_allow_negative_with_initial_remaining(self, test_user):
        """allow_negative flag is irrelevant when initial credits are positive."""
        m = test_user.membership
        m.initial_credits = 3
        m.purchased_credits = 0

        result = m.use_credit(allow_negative=True)

        assert result is True
        assert m.initial_credits == 2
        assert m.purchased_credits == 0

    def test_default_allow_negative_is_false(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0

        result = m.use_credit()

        assert result is False
        assert m.initial_credits == 0
        assert m.purchased_credits == 0


class TestUseCreditMembershipStatus:
    """Negative allowance is gated on active membership status."""

    def test_allow_negative_refused_for_pending_membership(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0
        m.status = "pending"

        result = m.use_credit(allow_negative=True)

        assert result is False
        assert m.initial_credits == 0

    def test_allow_negative_refused_for_expired_by_date(self, test_user):
        """Membership is 'active' status but expiry_date is in the past."""
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0
        m.status = "active"
        m.expiry_date = date.today() - timedelta(days=1)

        result = m.use_credit(allow_negative=True)

        assert result is False
        assert m.initial_credits == 0

    def test_allow_negative_accepted_on_expiry_day(self, test_user):
        """Membership expiring today is still considered active."""
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0
        m.status = "active"
        m.expiry_date = date.today()

        result = m.use_credit(allow_negative=True)

        assert result is True
        assert m.initial_credits == -1

    def test_inactive_membership_can_still_use_positive_credits(self, test_user):
        """Positive credits can be used regardless of membership status."""
        m = test_user.membership
        m.initial_credits = 5
        m.purchased_credits = 0
        m.status = "pending"

        result = m.use_credit()

        assert result is True
        assert m.initial_credits == 4

    def test_expired_by_date_can_still_use_positive_credits(self, test_user):
        """Positive credits usable even if membership has expired by date."""
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 3
        m.status = "active"
        m.expiry_date = date.today() - timedelta(days=30)

        result = m.use_credit()

        assert result is True
        assert m.purchased_credits == 2


class TestUseCreditInterleavedOperations:
    """Test use_credit interleaved with add_credits and remove_credits."""

    def test_add_credits_then_use(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0

        m.add_credits(3)
        result = m.use_credit()

        assert result is True
        # Purchased credits added, but initial is 0 so deduct from purchased
        assert m.initial_credits == 0
        assert m.purchased_credits == 2

    def test_use_credit_then_add_credits_restores_availability(self, test_user):
        m = test_user.membership
        m.initial_credits = 0
        m.purchased_credits = 0

        assert m.use_credit() is False

        m.add_credits(1)
        assert m.use_credit() is True
        assert m.purchased_credits == 0

    def test_negative_balance_then_add_credits_covers_debt(self, test_user):
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
