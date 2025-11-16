import pytest


class TestAuth:
    def test_login_valid_credentials(self, client, test_user):
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_invalid_credentials(self, client):
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })

        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_signup(self, client):
        response = client.post('/auth/signup', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'phone': '1234567890',
            'date_of_birth': '2000-01-01',
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Account created' in response.data
