class TestPublicPages:
    def test_index_page(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'South East Archers' in response.data or b'Archery' in response.data
    
    def test_about_page(self, client):
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About' in response.data
    
    def test_news_page(self, client, sample_news):
        response = client.get('/news')
        assert response.status_code == 200
        assert b'News' in response.data
    
    def test_news_detail(self, client, sample_news):
        news_id = sample_news[0].id
        response = client.get(f'/news/{news_id}')
        assert response.status_code == 200
        assert b'News Article 0' in response.data
    
    def test_events_page(self, client, sample_event):
        response = client.get('/events')
        assert response.status_code == 200
        assert b'Event' in response.data
    
    def test_event_detail(self, client, sample_event):
        event_id = sample_event.id
        response = client.get(f'/events/{event_id}')
        assert response.status_code == 200
        assert b'Test Event' in response.data
    
    def test_404_page(self, client):
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
