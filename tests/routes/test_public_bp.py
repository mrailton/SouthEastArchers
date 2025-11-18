"""Tests for public routes"""
import pytest
from datetime import date, timedelta
from app.models import News, Event


class TestPublicRoutes:
    def test_index_page(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_about_page(self, client):
        response = client.get('/about')
        assert response.status_code == 200

    def test_news_page(self, client, app):
        from app import db
        news = News(
            title='Test News',
            content='Test content',
            published=True,
            published_at=date.today()
        )
        db.session.add(news)
        db.session.commit()

        response = client.get('/news')
        assert response.status_code == 200
        assert b'Test News' in response.data

    def test_events_page(self, client, app):
        from app import db
        event = Event(
            title='Test Event',
            description='Test description',
            start_date=date.today() + timedelta(days=7),
            published=True
        )
        db.session.add(event)
        db.session.commit()

        response = client.get('/events')
        assert response.status_code == 200
        assert b'Test Event' in response.data
