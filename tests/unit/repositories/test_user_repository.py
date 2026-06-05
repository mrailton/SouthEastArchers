from app.models import User
from app.repositories import UserRepository


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


def test_user_repository_get_all_paginated(app, test_user, admin_user):
    """Test paginated user query"""
    result = UserRepository.get_all_paginated(page=1, per_page=10)
    assert result is not None
    assert result.total >= 2


def test_user_repository_get_all_paginated_with_search(app, test_user):
    """Test paginated search"""
    # Search by name
    result = UserRepository.get_all_paginated(page=1, per_page=10, search="Test")
    assert result.total >= 1

    # Search by email
    result = UserRepository.get_all_paginated(page=1, per_page=10, search="test@example.com")
    assert result.total >= 1


def test_user_repository_get_all_paginated_with_membership_filter(app, test_user):
    """Test membership filter"""
    # Users with membership
    result = UserRepository.get_all_paginated(page=1, per_page=10, membership_filter="with")
    assert result.total >= 1

    # Verify returned users have membership
    for user in result.items:
        assert user.membership is not None


def test_user_repository_get_all_paginated_without_membership(app):
    """Test filter for users without membership"""
    from app import db

    user = User(name="No Membership", email="nopmem@example.com", qualification="none")
    user.set_password("test123")
    db.session.add(user)
    db.session.commit()

    result = UserRepository.get_all_paginated(page=1, per_page=10, membership_filter="without")
    assert result.total >= 1

    # Verify returned users don't have membership
    for user in result.items:
        if user.email == "nopmem@example.com":
            assert user.membership is None


def test_user_repository_count_admins(app, admin_user):
    """Test counting admin users"""
    count = UserRepository.count_admins()
    assert count >= 1


def test_user_repository_count_pending(app):
    """Test counting pending users"""
    from app import db

    user = User(name="Pending", email="pending@example.com", qualification="none", is_active=False)
    user.set_password("test123")
    db.session.add(user)
    db.session.commit()

    count = UserRepository.count_pending_users()
    assert count >= 1


def test_user_repository_get_active_with_membership(app, test_user):
    """Test getting active users with membership"""
    users = UserRepository.get_active_with_membership()
    assert len(users) >= 1

    for user in users:
        assert user.is_active is True
        assert user.membership is not None


def test_user_repository_get_all_with_permission(app, admin_user):
    """Test getting users with specific permission"""
    users = UserRepository.get_all_with_permission("members.manage_membership")
    assert len(users) >= 1
