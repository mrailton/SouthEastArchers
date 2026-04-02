"""Repository for Setting model data access."""

from __future__ import annotations

from app import db
from app.models.application_settings import Setting
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    @staticmethod
    def get_value(key: str) -> str | None:
        """Return the raw string value for *key*, or ``None`` if not stored."""
        row = db.session.get(Setting, key)
        return row.value if row else None

    @staticmethod
    def set_value(key: str, value: str | None) -> None:
        """Upsert a single setting (does **not** commit)."""
        row = db.session.get(Setting, key)
        if row:
            row.value = value
        else:
            db.session.add(Setting(key=key, value=value))

    @staticmethod
    def get_all() -> dict[str, str | None]:
        """Return every stored setting as ``{key: raw_value}``."""
        rows = Setting.query.all()
        return {r.key: r.value for r in rows}
