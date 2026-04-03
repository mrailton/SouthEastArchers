from datetime import date, timedelta

from app import db
from app.models import Membership, User
from app.repositories import MembershipRepository


def test_membership_repository_count_active(app, test_user):
    count = MembershipRepository.count_active()
    assert count >= 1


def test_membership_repository_get_expired(app):
    user = User(name="Expired", email="expired_repo@example.com", qualification="none")
    user.set_password("test123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today() - timedelta(days=400),
        expiry_date=date.today() - timedelta(days=5),
        initial_credits=20,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    expired = MembershipRepository.get_expired()
    assert any(m.user_id == user.id for m in expired)
