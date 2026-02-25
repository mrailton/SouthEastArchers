"""Repository for News model data access."""

from __future__ import annotations

from app import db
from app.models import News
from app.repositories.base import BaseRepository


class NewsRepository(BaseRepository):
    @staticmethod
    def get_by_id(news_id: int) -> News | None:
        return db.session.get(News, news_id)

    @staticmethod
    def get_all() -> list[News]:
        return News.query.order_by(News.created_at.desc()).all()

    @staticmethod
    def get_published() -> list[News]:
        return News.query.filter_by(published=True).order_by(News.published_at.desc()).all()

    @staticmethod
    def add(news: News) -> None:
        db.session.add(news)
