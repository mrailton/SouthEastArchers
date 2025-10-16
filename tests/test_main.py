"""Test main routes."""
import pytest


class TestPublicPages:
    """Test public pages."""
    
    def test_index_page(self, client):
        """Test home page loads."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'South East Archers' in response.data or b'Archery' in response.data
    
    def test_about_page(self, client):
        """Test about page loads."""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About' in response.data
    
    def test_news_page(self, client, sample_news):
        """Test news page loads and shows articles."""
        response = client.get('/news')
        assert response.status_code == 200
        assert b'News' in response.data
    
    def test_news_detail(self, client, sample_news):
        """Test news detail page loads."""
        news_id = sample_news[0].id
        response = client.get(f'/news/{news_id}')
        assert response.status_code == 200
        assert b'News Article 0' in response.data
    
    def test_events_page(self, client, sample_event):
        """Test events page loads."""
        response = client.get('/events')
        assert response.status_code == 200
        assert b'Event' in response.data
    
    def test_event_detail(self, client, sample_event):
        """Test event detail page loads."""
        event_id = sample_event.id
        response = client.get(f'/events/{event_id}')
        assert response.status_code == 200
        assert b'Test Event' in response.data
    
    def test_404_page(self, client):
        """Test 404 error page."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
