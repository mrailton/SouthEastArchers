"""Tests for admin news management"""
import pytest
from app.models import News


class TestAdminNews:
    def test_news_list(self, client, admin_user):
        """Test viewing news list"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/news')
        assert response.status_code == 200

    def test_create_news_page(self, client, admin_user):
        """Test accessing create news page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/news/create')
        assert response.status_code == 200

    def test_edit_news_page(self, client, admin_user, app):
        """Test accessing edit news page"""
        from app import db
        
        news = News(
            title='Test News',
            content='Test content here',
            published=False
        )
        db.session.add(news)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get(f'/admin/news/{news.id}/edit')
        assert response.status_code == 200
        assert b'Edit News' in response.data
        assert b'Test News' in response.data

    def test_edit_news_success(self, client, admin_user, app):
        """Test updating news article"""
        from app import db
        
        news = News(
            title='Original Title',
            content='Original content',
            published=False
        )
        db.session.add(news)
        db.session.commit()
        news_id = news.id
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post(f'/admin/news/{news_id}/edit', data={
            'title': 'Updated Title',
            'summary': 'Updated summary',
            'content': 'Updated content here with more text',
            'published': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify changes
        updated_news = db.session.get(News, news_id)
        assert updated_news.title == 'Updated Title'
        assert updated_news.published is True
        assert updated_news.published_at is not None

    def test_edit_news_not_found(self, client, admin_user):
        """Test editing non-existent news"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/news/99999/edit')
        assert response.status_code == 404

    def test_news_requires_admin(self, client, test_user):
        """Test that news requires admin"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/admin/news')
        assert response.status_code in [302, 403]
