"""Repository for News model data access."""

from __future__ import annotations

from sqlalchemy import func, select

from app.db import db
from app.models import News
from app.repositories.base import BaseRepository


class NewsRepository(BaseRepository):
    @staticmethod
    def get_by_id(news_id: int) -> News | None:
        return db.session.get(News, news_id)

    @staticmethod
    def get_all() -> list[News]:
        stmt = select(News).order_by(News.created_at.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_published() -> list[News]:
        stmt = select(News).where(News.published.is_(True)).order_by(News.published_at.desc())
        return list(db.session.scalars(stmt).unique().all())

    @staticmethod
    def add(news: News) -> None:
        db.session.add(news)

    @staticmethod
    def count() -> int:
        return db.session.scalar(select(func.count()).select_from(News)) or 0
