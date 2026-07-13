from unittest.mock import patch

from app.models import News
from app.services import news


def test_get_published_articles(app):
    from app import db

    published = News(title="Pub", content="Published article content here.", published=False)
    published.publish()
    db.session.add_all(
        [
            published,
            News(title="Draft", content="Draft article content here.", published=False),
        ]
    )
    db.session.commit()
    articles = news.get_published_articles()
    assert len(articles) == 1
    assert articles[0].title == "Pub"


def test_create_article_success(app):
    result = news.create_article(
        title="New Story",
        summary="Summary",
        content="Story content with enough length.",
        published=True,
    )
    assert result.success is True
    assert result.data.published_at is not None


def test_create_article_failure(app):
    with patch("app.services.news.NewsRepository.save", side_effect=RuntimeError("db")):
        result = news.create_article(
            title="Fail Story",
            content="Story content with enough length.",
        )
    assert result.success is False
    assert "Error creating article" in result.message


def test_update_article_success(app):
    from app import db

    article = News(title="Old", content="Old content with enough length.", published=False)
    db.session.add(article)
    db.session.commit()
    result = news.update_article(article, title="Updated", content="Updated content with enough length.", published=True)
    assert result.success is True
    assert article.published_at is not None


def test_update_article_failure(app):
    from app import db

    article = News(title="Old", content="Old content with enough length.")
    db.session.add(article)
    db.session.commit()
    with patch("app.services.news.NewsRepository.save", side_effect=RuntimeError("db")):
        result = news.update_article(article, title="Updated")
    assert result.success is False
