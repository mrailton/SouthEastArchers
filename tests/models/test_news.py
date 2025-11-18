"""Tests for news model"""
import pytest
from app.models import News
from datetime import date


class TestNews:
    def test_create_news(self, app):
        from app import db
        news = News(
            title='Test News',
            content='Test content',
            published=True,
            published_at=date.today()
        )
        db.session.add(news)
        db.session.commit()
        
        assert news.id is not None
        assert news.title == 'Test News'
        assert news.published is True
