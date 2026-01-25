"""Tests for MembershipService - comprehensive service layer testing without mocks"""

from datetime import date, timedelta

import pytest

from app import db
from app.models import Membership, Payment, User
from app.services.membership_service import MembershipService


@pytest.fixture
def user_with_pending_membership(app):
    """Create a user with a pending membership"""
    user = User(name="Pending User", email="pending@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        status="pending",
        initial_credits=20,
        purchased_credits=0,
    )
    db.session.add(membership)
    db.session.commit()

    return user


@pytest.fixture
def user_with_cash_payment(app):
    """Create a user with pending cash payment"""
    user = User(name="Cash User", email="cash@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        status="pending",
        initial_credits=20,
        purchased_credits=0,
    )
    db.session.add(membership)

    payment = Payment(
        user_id=user.id,
        amount_cents=10000,
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    return user


# Activate membership tests
def test_activate_pending_membership(app, user_with_pending_membership):
    """Test activating a pending membership"""
    success, message = MembershipService.activate_membership(user_with_pending_membership)

    assert success is True
    assert "activated successfully" in message
    assert user_with_pending_membership.membership.status == "active"


def test_activate_with_pending_cash_payment(app, user_with_cash_payment):
    """Test activating membership also marks cash payment as completed"""
    success, message = MembershipService.activate_membership(user_with_cash_payment)

    assert success is True
    payment = Payment.query.filter_by(user_id=user_with_cash_payment.id, payment_type="membership", payment_method="cash").first()
    assert payment.status == "completed"


def test_activate_already_active_membership(app, test_user):
    """Test activating an already active membership fails"""
    assert test_user.membership.status == "active"

    success, message = MembershipService.activate_membership(test_user)

    assert success is False
    assert "already active" in message


def test_activate_user_without_membership(app):
    """Test activating membership for user without membership"""
    user = User(name="No Membership", email="nomem@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    success, message = MembershipService.activate_membership(user)

    assert success is False
    assert "No membership found" in message


# Renew membership tests
def test_renew_active_membership(app, test_user):
    """Test renewing an active membership"""
    success, message = MembershipService.renew_membership(test_user)

    assert success is True
    assert "renewed successfully" in message
    # When renewing, expiry is recalculated based on membership year settings
    # It may be shorter if renewing before year start (e.g., Jan renewal → Feb expiry)
    assert test_user.membership.expiry_date is not None
    assert test_user.membership.status == "active"


def test_renew_expired_membership(app, test_user):
    """Test renewing an expired membership"""
    # Set membership as expired
    test_user.membership.expiry_date = date.today() - timedelta(days=10)
    test_user.membership.status = "inactive"
    db.session.commit()

    success, message = MembershipService.renew_membership(test_user)

    assert success is True
    # Expiry is calculated based on membership year, not +365 days
    # If renewing before year start, may get less than a full year
    assert test_user.membership.expiry_date >= date.today()
    assert test_user.membership.status == "active"


def test_renew_user_without_membership(app):
    """Test renewing membership for user without membership"""
    user = User(name="No Membership", email="nomem2@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    success, message = MembershipService.renew_membership(user)

    assert success is False
    assert "No membership to renew" in message


# Deactivate membership tests
def test_deactivate_active_membership(app, test_user):
    """Test deactivating an active membership"""
    assert test_user.membership.status == "active"

    success, message = MembershipService.deactivate_membership(test_user)

    assert success is True
    assert "deactivated successfully" in message
    assert test_user.membership.status == "inactive"


def test_deactivate_already_inactive_membership(app, test_user):
    """Test deactivating an already inactive membership"""
    test_user.membership.status = "inactive"
    db.session.commit()

    success, message = MembershipService.deactivate_membership(test_user)

    assert success is True
    assert test_user.membership.status == "inactive"


def test_deactivate_user_without_membership(app):
    """Test deactivating membership for user without membership"""
    user = User(name="No Membership", email="nomem3@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    success, message = MembershipService.deactivate_membership(user)

    assert success is False
    assert "No membership found" in message


# Get expiring memberships tests
def test_get_expiring_memberships_default_30_days(app):
    """Test getting memberships expiring in 30 days (includes already expired)"""
    # Create users with different expiry dates
    users_data = [
        ("Expiring Soon 1", "exp1@example.com", date.today() + timedelta(days=15)),
        ("Expiring Soon 2", "exp2@example.com", date.today() + timedelta(days=29)),
        ("Not Expiring", "notexp@example.com", date.today() + timedelta(days=60)),
        ("Already Expired", "expired@example.com", date.today() - timedelta(days=5)),
    ]

    created_users = []
    for name, email, expiry in users_data:
        user = User(name=name, email=email)
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today() - timedelta(days=335),
            expiry_date=expiry,
            status="active",
            initial_credits=20,
            purchased_credits=0,
        )
        db.session.add(membership)
        created_users.append(email)

    db.session.commit()

    result = MembershipService.get_expiring_memberships()

    # Filter to only the users we created in this test
    # Function returns all memberships with expiry <= today+30, including already expired
    result_emails = [m.user.email for m in result if m.user.email in created_users]
    assert len(result_emails) == 3  # Includes the expired one
    assert "exp1@example.com" in result_emails
    assert "exp2@example.com" in result_emails
    assert "expired@example.com" in result_emails  # Already expired ones are included


def test_get_expiring_memberships_custom_days(app):
    """Test getting memberships expiring in custom number of days"""
    user = User(name="Expiring 7", email="exp7@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today() - timedelta(days=358),
        expiry_date=date.today() + timedelta(days=5),
        status="active",
        initial_credits=20,
        purchased_credits=0,
    )
    db.session.add(membership)
    db.session.commit()

    result = MembershipService.get_expiring_memberships(days=7)

    assert len(result) == 1
    assert result[0].user.email == "exp7@example.com"


def test_get_expiring_memberships_excludes_inactive(app):
    """Test that inactive memberships are excluded"""
    user = User(name="Inactive Expiring", email="inactexp@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today() - timedelta(days=335),
        expiry_date=date.today() + timedelta(days=15),
        status="inactive",
        initial_credits=20,
        purchased_credits=0,
    )
    db.session.add(membership)
    db.session.commit()

    result = MembershipService.get_expiring_memberships()

    assert len(result) == 0


# Get expired memberships tests
def test_get_expired_memberships(app):
    """Test getting expired but still active-status memberships"""
    users_data = [
        ("Expired 1", "exp1@example.com", date.today() - timedelta(days=5)),
        ("Expired 2", "exp2@example.com", date.today() - timedelta(days=30)),
        ("Not Expired", "notexp@example.com", date.today() + timedelta(days=30)),
    ]

    for name, email, expiry in users_data:
        user = User(name=name, email=email)
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        membership = Membership(
            user_id=user.id,
            start_date=date.today() - timedelta(days=365),
            expiry_date=expiry,
            status="active",
            initial_credits=20,
            purchased_credits=0,
        )
        db.session.add(membership)

    db.session.commit()

    result = MembershipService.get_expired_memberships()

    assert len(result) == 2
    emails = [m.user.email for m in result]
    assert "exp1@example.com" in emails
    assert "exp2@example.com" in emails
    assert "notexp@example.com" not in emails


def test_get_expired_memberships_excludes_already_inactive(app):
    """Test that memberships marked as inactive are excluded"""
    user = User(name="Inactive Expired", email="inacexp@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today() - timedelta(days=365),
        expiry_date=date.today() - timedelta(days=30),
        status="inactive",
        initial_credits=20,
        purchased_credits=0,
    )
    db.session.add(membership)
    db.session.commit()

    result = MembershipService.get_expired_memberships()

    assert len(result) == 0
