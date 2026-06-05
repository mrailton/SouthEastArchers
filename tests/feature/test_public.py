"""Public routes — feature flags and published content filtering."""

from datetime import date, timedelta

from app import db
from app.models import Event, News
from app.services.settings_service import SettingsService


def _enable_features() -> None:
    SettingsService.set("news_enabled", True)
    SettingsService.set("events_enabled", True)


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"South East Archers" in response.content


def test_events_only_shows_published(client, app):
    _enable_features()
    db.session.add_all(
        [
            Event(
                title="Published Event",
                description="Visible",
                start_date=date.today() + timedelta(days=7),
                published=True,
            ),
            Event(
                title="Unpublished Event",
                description="Hidden",
                start_date=date.today() + timedelta(days=7),
                published=False,
            ),
        ]
    )
    db.session.commit()

    response = client.get("/events")
    assert b"Published Event" in response.content
    assert b"Unpublished Event" not in response.content


def test_news_detail_unpublished_returns_404(client, app):
    _enable_features()
    news = News(title="Draft", content="Hidden draft content here.", published=False)
    db.session.add(news)
    db.session.commit()

    response = client.get(f"/news/{news.id}")
    assert response.status_code == 404


def test_news_disabled_returns_404(client, app):
    response = client.get("/news")
    assert response.status_code == 404


def test_events_disabled_returns_404(client, app):
    response = client.get("/events")
    assert response.status_code == 404
