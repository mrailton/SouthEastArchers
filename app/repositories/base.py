"""Base repository with shared transaction management."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from app.db import db


class BaseRepository:
    @staticmethod
    def save() -> None:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    @contextmanager
    def transaction() -> Generator[None]:
        try:
            yield
        except Exception:
            db.session.rollback()
            raise
        else:
            BaseRepository.save()

    @staticmethod
    def flush() -> None:
        db.session.flush()

    @staticmethod
    def drop_all() -> None:
        db.drop_all()

    @staticmethod
    def create_all() -> None:
        db.create_all()
