"""Tests for repository layer."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app import db
from app.models import (
    Credit,
    Event,
    Membership,
    News,
    Payment,
    Shoot,
    User,
)
from app.models.application_settings import ApplicationSettings
from app.repositories import (
    BaseRepository,
    CreditRepository,
    EventRepository,
    MembershipRepository,
    NewsRepository,
    PaymentRepository,
    RBACRepository,
    SettingsRepository,
    ShootRepository,
    UserRepository,
)

# =============================================================================
# BaseRepository – save() contract
# =============================================================================


def test_base_repository_save_commits(app):
    """save() commits the session on success."""
    user = User(name="Save Test", email="savetest@example.com", qualification="none")
    user.set_password("test123")
    db.session.add(user)

    BaseRepository.save()

    found = User.query.filter_by(email="savetest@example.com").first()
    assert found is not None


def test_base_repository_save_rolls_back_and_reraises_on_error(app):
    """save() rolls back the session and re-raises the exception on failure."""
    with patch("app.repositories.base.db.session.commit", side_effect=Exception("boom")):
        with pytest.raises(Exception, match="boom"):
            BaseRepository.save()


def test_base_repository_save_rollback_cleans_session(app):
    """After save() fails, the session is rolled back so subsequent operations work."""
    user = User(name="Rollback Test", email="rollback@example.com", qualification="none")
    user.set_password("test123")
    db.session.add(user)

    with patch("app.repositories.base.db.session.commit", side_effect=Exception("boom")):
        with pytest.raises(Exception):
            BaseRepository.save()

    # Session should be clean after rollback — new operations should work
    user2 = User(name="After Rollback", email="after@example.com", qualification="none")
    user2.set_password("test123")
    db.session.add(user2)
    BaseRepository.save()

    assert User.query.filter_by(email="after@example.com").first() is not None
    # The first user should NOT have been saved
    assert User.query.filter_by(email="rollback@example.com").first() is None


# =============================================================================
# UserRepository
# =============================================================================


def test_user_repository_get_by_id(app, test_user):
    result = UserRepository.get_by_id(test_user.id)
    assert result is not None
    assert result.email == test_user.email


def test_user_repository_get_by_id_not_found(app):
    result = UserRepository.get_by_id(99999)
    assert result is None


def test_user_repository_get_by_email(app, test_user):
    result = UserRepository.get_by_email(test_user.email)
    assert result is not None
    assert result.id == test_user.id


def test_user_repository_get_by_email_not_found(app):
    result = UserRepository.get_by_email("nonexistent@example.com")
    assert result is None


def test_user_repository_get_all(app, test_user, admin_user):
    users = UserRepository.get_all()
    assert len(users) >= 2


def test_user_repository_count(app, test_user):
    count = UserRepository.count()
    assert count >= 1


def test_user_repository_get_recent(app, test_user):
    recent = UserRepository.get_recent(limit=5)
    assert len(recent) >= 1


def test_user_repository_crud(app):
    user = User(name="Repo User", email="repo@example.com", qualification="none")
    user.set_password("test123")
    UserRepository.add(user)
    UserRepository.flush()
    assert user.id is not None
    UserRepository.save()

    found = UserRepository.get_by_id(user.id)
    assert found is not None
    assert found.name == "Repo User"

    UserRepository.delete(user)
    UserRepository.save()
    assert UserRepository.get_by_id(user.id) is None


# =============================================================================
# MembershipRepository
# =============================================================================


def test_membership_repository_count_active(app, test_user):
    count = MembershipRepository.count_active()
    assert count >= 1


def test_membership_repository_count_expiring_soon(app, test_user):
    # test_user has membership expiring in 335 days, so not expiring soon
    count = MembershipRepository.count_expiring_soon(days=30)
    assert count >= 0


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


# =============================================================================
# PaymentRepository
# =============================================================================


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


# =============================================================================
# CreditRepository
# =============================================================================


def test_credit_repository_get_by_user(app, test_user):
    credit = Credit(user_id=test_user.id, amount=5)
    CreditRepository.add(credit)
    CreditRepository.save()

    credits = CreditRepository.get_by_user(test_user.id)
    assert len(credits) >= 1


# =============================================================================
# EventRepository
# =============================================================================


def test_event_repository_get_all(app):
    from app.utils.datetime_utils import utc_now

    event = Event(title="Repo Event", description="Test", start_date=utc_now())
    db.session.add(event)
    db.session.commit()

    events = EventRepository.get_all()
    assert len(events) >= 1


def test_event_repository_get_by_id(app):
    from app.utils.datetime_utils import utc_now

    event = Event(title="Find Me", description="Test", start_date=utc_now())
    db.session.add(event)
    db.session.commit()

    found = EventRepository.get_by_id(event.id)
    assert found is not None
    assert found.title == "Find Me"


# =============================================================================
# NewsRepository
# =============================================================================


def test_news_repository_get_all(app):
    article = News(title="Repo News", content="Test content")
    db.session.add(article)
    db.session.commit()

    articles = NewsRepository.get_all()
    assert len(articles) >= 1


def test_news_repository_get_published(app):
    from app.utils.datetime_utils import utc_now

    article = News(title="Published News", content="Content", published=True, published_at=utc_now())
    db.session.add(article)
    db.session.commit()

    published = NewsRepository.get_published()
    assert len(published) >= 1


# =============================================================================
# ShootRepository
# =============================================================================


def test_shoot_repository_get_all(app):
    from app.models.shoot import ShootLocation

    shoot = Shoot(date=date.today(), location=ShootLocation.HALL)
    db.session.add(shoot)
    db.session.commit()

    shoots = ShootRepository.get_all()
    assert len(shoots) >= 1


# =============================================================================
# RBACRepository
# =============================================================================


def test_rbac_repository_list_roles(app):
    roles = RBACRepository.list_roles()
    assert len(roles) >= 1


def test_rbac_repository_list_permissions(app):
    perms = RBACRepository.list_permissions()
    assert len(perms) >= 1


def test_rbac_repository_role_name_exists(app):
    assert RBACRepository.role_name_exists("Admin")
    assert not RBACRepository.role_name_exists("NonexistentRole")


def test_rbac_repository_get_permissions_by_ids(app):
    all_perms = RBACRepository.list_permissions()
    ids = [p.id for p in all_perms[:2]]
    result = RBACRepository.get_permissions_by_ids(ids)
    assert len(result) == 2


# =============================================================================
# SettingsRepository
# =============================================================================


def test_settings_repository_get(app):
    settings = SettingsRepository.get()
    # May be None if not seeded, but shouldn't error
    # If it exists, should be an ApplicationSettings instance
    if settings:
        assert isinstance(settings, ApplicationSettings)


def test_settings_repository_add_and_commit(app):
    if SettingsRepository.get() is None:
        settings = ApplicationSettings()
        SettingsRepository.add(settings)
        SettingsRepository.save()
        assert SettingsRepository.get() is not None
