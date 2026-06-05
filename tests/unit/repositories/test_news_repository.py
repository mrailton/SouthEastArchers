from app import db
from app.models import News
from app.repositories import NewsRepository
from app.utils.datetime_utils import utc_now


def test_news_repository_get_all(app):
    article = News(title="Repo News", content="Test content")
    db.session.add(article)
    db.session.commit()

    articles = NewsRepository.get_all()
    assert len(articles) >= 1


def test_news_repository_get_published(app):
    article = News(title="Published News", content="Content", published=True, published_at=utc_now())
    db.session.add(article)
    db.session.commit()

    published = NewsRepository.get_published()
    assert len(published) >= 1
