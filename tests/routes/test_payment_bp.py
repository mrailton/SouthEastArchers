"""Tests for payment routes"""
import pytest


class TestPaymentRoutes:
    def test_credits_page_requires_login(self, client):
        response = client.get('/payment/credits', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_credits_page_logged_in(self, client, test_user):
        with client:
            client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'password123'
            })
            
            response = client.get('/payment/credits')
            assert response.status_code == 200
