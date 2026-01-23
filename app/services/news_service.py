from app import db
from app.models import News
from app.utils.datetime_utils import utc_now


class NewsService:
    @staticmethod
    def create_article(
        title: str,
        summary: str = None,
        content: str = None,
        published: bool = False,
    ) -> News:
        """Create a new news article."""
        article = News(
            title=title,
            summary=summary,
            content=content,
            published=published,
        )

        if published:
            article.published_at = utc_now()

        db.session.add(article)
        db.session.commit()
        return article

    @staticmethod
    def update_article(
        article: News,
        title: str,
        summary: str = None,
        content: str = None,
        published: bool = False,
    ) -> News:
        """Update an existing news article."""
        article.title = title
        article.summary = summary
        article.content = content
        article.published = published

        if published and not article.published_at:
            article.published_at = utc_now()

        db.session.commit()
        return article

    @staticmethod
    def get_all_articles() -> list[News]:
        """Get all news articles ordered by creation date descending."""
        return News.query.order_by(News.created_at.desc()).all()

    @staticmethod
    def get_published_articles() -> list[News]:
        """Get all published articles ordered by publish date descending."""
        return News.query.filter_by(published=True).order_by(News.published_at.desc()).all()

    @staticmethod
    def get_article_by_id(news_id: int) -> News | None:
        """Get a news article by ID."""
        return db.session.get(News, news_id)
