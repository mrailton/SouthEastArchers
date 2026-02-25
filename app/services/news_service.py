from app.models import News
from app.repositories import NewsRepository
from app.utils.datetime_utils import utc_now


class NewsService:
    @staticmethod
    def create_article(
        title: str,
        summary: str = None,
        content: str = None,
        published: bool = False,
    ) -> tuple[News | None, str | None]:
        """Create a new news article."""
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
            return article, None
        except Exception as e:
            return None, f"Error creating article: {str(e)}"

    @staticmethod
    def update_article(
        article: News,
        title: str,
        summary: str = None,
        content: str = None,
        published: bool = False,
    ) -> tuple[bool, str | None]:
        """Update an existing news article."""
        article.title = title
        article.summary = summary
        article.content = content
        article.published = published

        if published and not article.published_at:
            article.published_at = utc_now()

        try:
            NewsRepository.save()
            return True, None
        except Exception as e:
            return False, f"Error updating article: {str(e)}"

    @staticmethod
    def get_all_articles() -> list[News]:
        """Get all news articles ordered by creation date descending."""
        return NewsRepository.get_all()

    @staticmethod
    def get_published_articles() -> list[News]:
        """Get all published articles ordered by publish date descending."""
        return NewsRepository.get_published()

    @staticmethod
    def get_article_by_id(news_id: int) -> News | None:
        """Get a news article by ID."""
        return NewsRepository.get_by_id(news_id)
