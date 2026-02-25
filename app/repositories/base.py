"""Base repository with shared transaction management."""

from __future__ import annotations

from app import db


class BaseRepository:
    """Provides common database operations for all repositories.

    Subclasses inherit ``save()``, ``flush()``, and ``delete()`` so that
    transaction management is centralised.  On commit failure the session
    is rolled back and the exception is re-raised so the calling service
    can translate it into a user-facing message.
    """

    @staticmethod
    def save() -> None:
        """Commit the current session.  Rolls back and re-raises on error."""
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def flush() -> None:
        db.session.flush()
