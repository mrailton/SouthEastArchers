"""Tests for ShootService – negative-credit edge cases.

The allow_negative=True path is used by admin bookings so members can be
recorded on a shoot even when they have exhausted their credits.  These
tests verify the service-layer behaviour: correct credit deduction, warning
generation, and interaction with membership status.
"""

from datetime import date, timedelta

from app import db
from app.models import Membership, User
from app.services import ShootService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_member(*, name, email, initial_credits=0, purchased_credits=0, status="active", expiry_offset_days=335):
    """Create a user with a membership and return the user."""
    user = User(name=name, email=email, phone="0000000000", is_active=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=expiry_offset_days),
        initial_credits=initial_credits,
        purchased_credits=purchased_credits,
        status=status,
    )
    db.session.add(membership)
    db.session.commit()
    return user


# ---------------------------------------------------------------------------
# create_shoot – negative credit scenarios
# ---------------------------------------------------------------------------


class TestCreateShootNegativeCredits:
    """ShootService.create_shoot with allow_negative=True (admin booking)."""

    def test_zero_credits_goes_negative(self, app):
        """Attendee with 0 credits goes to -1 and a warning is emitted."""
        user = _create_member(name="Zero Credits", email="zero@test.com", initial_credits=0)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert len(result.data.users) == 1
        assert user.membership.credits_remaining() == -1
        assert len(result.warnings) == 1
        assert "negative balance" in result.warnings[0].lower()

    def test_already_negative_goes_more_negative(self, app):
        """Attendee starting at -3 credits drops to -4."""
        user = _create_member(name="Deep Negative", email="deep@test.com", initial_credits=-3)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == -4
        assert any("-4 credits" in w for w in result.warnings)

    def test_multiple_attendees_mixed_credits(self, app):
        """One user has credits, another doesn't — only the zero-credit user gets a warning."""
        rich = _create_member(name="Rich User", email="rich@test.com", initial_credits=10)
        broke = _create_member(name="Broke User", email="broke@test.com", initial_credits=0)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="MEADOW",
            attendee_ids=[rich.id, broke.id],
        )

        assert result.success is True
        assert len(result.data.users) == 2
        assert rich.membership.credits_remaining() == 9
        assert broke.membership.credits_remaining() == -1
        assert len(result.warnings) == 1
        assert "Broke User" in result.warnings[0]

    def test_inactive_membership_cannot_go_negative(self, app):
        """Pending membership with zero credits is refused (allow_negative gates on is_active)."""
        user = _create_member(
            name="Pending Member",
            email="pending@test.com",
            initial_credits=0,
            status="pending",
        )

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert len(result.data.users) == 0
        assert user.membership.credits_remaining() == 0
        assert len(result.warnings) == 1
        assert "cannot be added" in result.warnings[0].lower()

    def test_expired_membership_cannot_go_negative(self, app):
        """Active-status but date-expired membership is refused for negative credits."""
        user = _create_member(
            name="Expired Member",
            email="expired@test.com",
            initial_credits=0,
            expiry_offset_days=-1,  # expired yesterday
        )

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert len(result.data.users) == 0
        assert user.membership.credits_remaining() == 0
        assert "cannot be added" in result.warnings[0].lower()

    def test_last_credit_no_warning(self, app):
        """Using the last credit (1 → 0) succeeds with no warning (not negative)."""
        user = _create_member(name="Last Credit", email="last@test.com", initial_credits=1)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="WOODS",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == 0
        assert len(result.warnings) == 0

    def test_all_attendees_zero_credits(self, app):
        """Multiple attendees all with zero credits — each gets a warning."""
        users = [_create_member(name=f"User {i}", email=f"user{i}@test.com", initial_credits=0) for i in range(3)]

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[u.id for u in users],
        )

        assert result.success is True
        assert len(result.data.users) == 3
        assert len(result.warnings) == 3
        for u in users:
            assert u.membership.credits_remaining() == -1

    def test_purchased_credits_used_before_going_negative(self, app):
        """User with 0 initial but 1 purchased credit uses purchased first — no negative."""
        user = _create_member(
            name="Purchased Only",
            email="purchased@test.com",
            initial_credits=0,
            purchased_credits=1,
        )

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == 0
        assert user.membership.purchased_credits == 0
        assert len(result.warnings) == 0


# ---------------------------------------------------------------------------
# update_shoot – negative credit scenarios
# ---------------------------------------------------------------------------


class TestUpdateShootNegativeCredits:
    """ShootService.update_shoot with allow_negative=True (admin editing)."""

    def test_add_zero_credit_attendee(self, app):
        """Adding a zero-credit attendee via update goes negative with warning."""
        user = _create_member(name="Zero Update", email="zeroup@test.com", initial_credits=0)

        create_result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            description="Empty shoot",
        )
        shoot = create_result.data

        result = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == -1
        assert len(result.warnings) == 1
        assert "negative balance" in result.warnings[0].lower()

    def test_add_already_negative_attendee(self, app):
        """Adding attendee who is already at -2 credits drops them to -3."""
        user = _create_member(name="Neg Update", email="negup@test.com", initial_credits=-2)

        create_result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
        )
        shoot = create_result.data

        result = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == -3
        assert any("-3 credits" in w for w in result.warnings)

    def test_remove_negative_attendee_refunds_credit(self, app):
        """Removing an attendee who went negative refunds a purchased credit."""
        user = _create_member(name="Refund User", email="refund@test.com", initial_credits=0)

        # Create shoot with user (goes to -1)
        create_result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )
        shoot = create_result.data
        assert user.membership.credits_remaining() == -1

        # Remove the user from the shoot
        result = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[],  # remove all
        )

        assert result.success is True
        # Refund adds 1 purchased credit: initial=-1 + purchased=1 = 0
        assert user.membership.credits_remaining() == 0
        assert user.membership.purchased_credits == 1
        assert user.membership.initial_credits == -1

    def test_swap_attendees_one_negative(self, app):
        """Swap: remove member with credits, add member without — only new member warned."""
        rich = _create_member(name="Rich Swap", email="richswap@test.com", initial_credits=5)
        broke = _create_member(name="Broke Swap", email="brokeswap@test.com", initial_credits=0)

        create_result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[rich.id],
        )
        shoot = create_result.data
        assert rich.membership.credits_remaining() == 4

        result = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[broke.id],  # swap rich → broke
        )

        assert result.success is True
        # Rich gets refund: 4 + 1 = 5
        assert rich.membership.credits_remaining() == 5
        # Broke goes negative
        assert broke.membership.credits_remaining() == -1
        assert len(result.warnings) == 1
        assert "Broke Swap" in result.warnings[0]

    def test_inactive_membership_refused_on_update(self, app):
        """Pending member cannot be added via update either."""
        user = _create_member(
            name="Pending Update",
            email="pendingup@test.com",
            initial_credits=0,
            status="pending",
        )

        create_result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
        )
        shoot = create_result.data

        result = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == 0
        assert len(result.warnings) == 1
        assert "cannot be added" in result.warnings[0].lower()

    def test_expired_membership_refused_on_update(self, app):
        """Date-expired member cannot go negative via update."""
        user = _create_member(
            name="Expired Update",
            email="expup@test.com",
            initial_credits=0,
            expiry_offset_days=-10,
        )

        create_result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
        )
        shoot = create_result.data

        result = ShootService.update_shoot(
            shoot=shoot,
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert result.success is True
        assert user.membership.credits_remaining() == 0
        assert "cannot be added" in result.warnings[0].lower()


# ---------------------------------------------------------------------------
# Warning message content
# ---------------------------------------------------------------------------


class TestNegativeCreditWarnings:
    """Verify warning messages contain the expected information."""

    def test_warning_includes_user_name(self, app):
        user = _create_member(name="Alice Archer", email="alice@test.com", initial_credits=0)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert "Alice Archer" in result.warnings[0]

    def test_warning_includes_credit_count(self, app):
        user = _create_member(name="Bob Bowman", email="bob@test.com", initial_credits=0)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert "-1 credits" in result.warnings[0]

    def test_deeply_negative_warning(self, app):
        """User at -9 going to -10 — warning shows correct count."""
        user = _create_member(name="Deep Debt", email="debt@test.com", initial_credits=-9)

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert "-10 credits" in result.warnings[0]

    def test_inactive_warning_message(self, app):
        user = _create_member(
            name="Inactive Ian",
            email="ian@test.com",
            initial_credits=0,
            status="pending",
        )

        result = ShootService.create_shoot(
            shoot_date=date.today(),
            location="HALL",
            attendee_ids=[user.id],
        )

        assert "Inactive Ian" in result.warnings[0]
        assert "cannot be added" in result.warnings[0].lower()
        assert "inactive membership" in result.warnings[0].lower()
