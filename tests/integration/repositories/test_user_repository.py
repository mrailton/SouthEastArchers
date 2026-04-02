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
