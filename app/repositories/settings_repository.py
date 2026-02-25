"""Repository for ApplicationSettings model data access."""

from __future__ import annotations

from app import db
from app.models.application_settings import ApplicationSettings
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    @staticmethod
    def get() -> ApplicationSettings | None:
        return ApplicationSettings.query.first()

    @staticmethod
    def add(settings: ApplicationSettings) -> None:
        db.session.add(settings)
