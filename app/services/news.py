from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news import News
from app.repositories import NewsRepository
from app.services.result import ServiceResult
from app.utils.datetime_utils import utc_now


def get_published_articles(db: Session) -> list[News]:
    return list(db.scalars(select(News).where(News.published.is_(True)).order_by(News.published_at.desc())).all())


def get_article_by_id(news_id: int, db: Session | None = None) -> News | None:
    if db is not None:
        return db.get(News, news_id)
    return NewsRepository.get_by_id(news_id)


def create_article(
    title: str,
    summary: str | None = None,
    content: str | None = None,
    published: bool = False,
) -> ServiceResult[News]:
    article = News(
        title=title,
        summary=summary,
        content=content,
        published=published,
    )

    if published:
        article.published_at = utc_now()

    try:
        NewsRepository.add(article)
        NewsRepository.save()
        return ServiceResult.ok(data=article)
    except Exception as exc:
        return ServiceResult.fail(f"Error creating article: {exc}")


def update_article(
    article: News,
    title: str,
    summary: str | None = None,
    content: str | None = None,
    published: bool = False,
) -> ServiceResult[None]:
    article.title = title
    article.summary = summary
    article.content = content
    article.published = published

    if published and not article.published_at:
        article.published_at = utc_now()

    try:
        NewsRepository.save()
        return ServiceResult.ok()
    except Exception as exc:
        return ServiceResult.fail(f"Error updating article: {exc}")


def get_all_articles() -> list[News]:
    return NewsRepository.get_all()
