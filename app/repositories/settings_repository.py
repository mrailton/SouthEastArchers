"""Repository for Setting model data access."""

from __future__ import annotations

from sqlalchemy import select

from app.db import db
from app.models.application_settings import Setting
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    @staticmethod
    def get_value(key: str) -> str | None:
        row = db.session.get(Setting, key)
        return row.value if row else None

    @staticmethod
    def set_value(key: str, value: str | None) -> None:
        row = db.session.get(Setting, key)
        if row:
            row.value = value
        else:
            db.session.add(Setting(key=key, value=value))

    @staticmethod
    def get_all() -> dict[str, str | None]:
        rows = db.session.scalars(select(Setting)).unique().all()
        return {row.key: row.value for row in rows}
