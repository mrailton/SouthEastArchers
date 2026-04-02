from unittest.mock import patch

import pytest

from app import db
from app.models import User
from app.repositories import BaseRepository


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
