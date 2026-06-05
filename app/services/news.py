from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news import News


def get_published_articles(db: Session) -> list[News]:
    return list(db.scalars(select(News).where(News.published.is_(True)).order_by(News.published_at.desc())).all())


def get_article_by_id(db: Session, news_id: int) -> News | None:
    return db.get(News, news_id)
