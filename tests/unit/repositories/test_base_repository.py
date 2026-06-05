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


# ---------------------------------------------------------------------------
# BaseRepository.transaction()
# ---------------------------------------------------------------------------


def test_transaction_commits_on_clean_exit(app):
    """transaction() commits all mutations when the block exits cleanly."""
    user = User(name="Txn Test", email="txn@example.com", qualification="none")
    user.set_password("test123")

    with BaseRepository.transaction():
        db.session.add(user)

    assert User.query.filter_by(email="txn@example.com").first() is not None


def test_transaction_rolls_back_on_body_exception(app):
    """transaction() rolls back and re-raises if the block raises."""
    user = User(name="Txn Fail", email="txnfail@example.com", qualification="none")
    user.set_password("test123")

    with pytest.raises(ValueError, match="oops"):
        with BaseRepository.transaction():
            db.session.add(user)
            raise ValueError("oops")

    assert User.query.filter_by(email="txnfail@example.com").first() is None


def test_transaction_rolls_back_on_commit_failure(app):
    """transaction() rolls back when the underlying commit fails."""
    user = User(name="Commit Fail", email="commitfail@example.com", qualification="none")
    user.set_password("test123")

    with patch("app.repositories.base.db.session.commit", side_effect=Exception("db down")):
        with pytest.raises(Exception, match="db down"):
            with BaseRepository.transaction():
                db.session.add(user)

    assert User.query.filter_by(email="commitfail@example.com").first() is None


def test_transaction_session_usable_after_rollback(app):
    """After a failed transaction the session is clean for subsequent work."""
    with pytest.raises(RuntimeError):
        with BaseRepository.transaction():
            db.session.add(User(name="Bad", email="bad@example.com", qualification="none"))
            raise RuntimeError("fail")

    # Session should still be usable
    user = User(name="Good", email="good@example.com", qualification="none")
    user.set_password("test123")
    with BaseRepository.transaction():
        db.session.add(user)

    assert User.query.filter_by(email="good@example.com").first() is not None
    assert User.query.filter_by(email="bad@example.com").first() is None
