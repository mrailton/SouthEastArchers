"""Tests for public routes"""

from datetime import date, timedelta

import pytest

from app.models import Event, News


class TestPublicRoutes:
    def test_index_page(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_about_page(self, client):
        response = client.get("/about")
        assert response.status_code == 200

    def test_news_page(self, client, app):
        from app import db

        news = News(
            title="Test News",
            content="Test content",
            published=True,
            published_at=date.today(),
        )
        db.session.add(news)
        db.session.commit()

        response = client.get("/news")
        assert response.status_code == 200
        assert b"Test News" in response.data

    def test_events_page(self, client, app):
        from app import db

        event = Event(
            title="Test Event",
            description="Test description",
            start_date=date.today() + timedelta(days=7),
            published=True,
        )
        db.session.add(event)
        db.session.commit()

        response = client.get("/events")
        assert response.status_code == 200
        assert b"Test Event" in response.data

    def test_events_page_no_events(self, client):
        """Test events page when no events exist"""
        response = client.get("/events")
        assert response.status_code == 200

    def test_events_only_shows_published(self, client, app):
        """Test that only published events are shown"""
        from app import db

        event1 = Event(
            title="Published Event",
            description="Should be visible",
            start_date=date.today() + timedelta(days=7),
            published=True,
        )
        event2 = Event(
            title="Unpublished Event",
            description="Should not be visible",
            start_date=date.today() + timedelta(days=7),
            published=False,
        )
        db.session.add_all([event1, event2])
        db.session.commit()

        response = client.get("/events")
        assert response.status_code == 200
        assert b"Published Event" in response.data
        assert b"Unpublished Event" not in response.data

    def test_news_only_shows_published(self, client, app):
        """Test that only published news are shown"""
        from app import db

        news1 = News(
            title="Published News",
            content="Published content",
            published=True,
            published_at=date.today(),
        )
        news2 = News(title="Unpublished News", content="Unpublished content", published=False)
        db.session.add_all([news1, news2])
        db.session.commit()

        response = client.get("/news")
        assert response.status_code == 200
        assert b"Published News" in response.data
        assert b"Unpublished News" not in response.data

    def test_news_detail_valid(self, client, app):
        """Test viewing a valid news article"""
        from app import db

        news = News(
            title="Detailed News",
            content="This is detailed news content",
            published=True,
            published_at=date.today(),
        )
        db.session.add(news)
        db.session.commit()

        response = client.get(f"/news/{news.id}")
        assert response.status_code == 200
        assert b"Detailed News" in response.data
        assert b"detailed news content" in response.data

    def test_news_detail_not_found(self, client):
        """Test viewing non-existent news article"""
        response = client.get("/news/99999")
        assert response.status_code == 404

    def test_news_detail_unpublished(self, client, app):
        """Test viewing unpublished news article returns 404"""
        from app import db

        news = News(
            title="Unpublished News",
            content="This should not be visible",
            published=False,
        )
        db.session.add(news)
        db.session.commit()

        response = client.get(f"/news/{news.id}")
        assert response.status_code == 404

    def test_membership_info_page(self, client):
        """Test membership information page"""
        response = client.get("/membership")
        assert response.status_code == 200

    def test_news_page_empty(self, client):
        """Test news page when no news exists"""
        response = client.get("/news")
        assert response.status_code == 200
