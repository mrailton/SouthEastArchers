from app.models import User


class TestRegistration:
    def test_registration(self, client, app):
        response = client.get('/auth/register')
        assert response.status_code == 200

        response = client.post('/auth/register', data={
            'email': 'newuser@test.com',
            'name': 'New User',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        user = User.query.filter_by(email='newuser@test.com').first()
        assert user is not None

    def test_registration_existing_email(self, client, app, regular_user):
        response = client.post('/auth/register', data={
            'email': 'user@test.com',
            'name': 'Another User',
            'password': 'password456',
            'password2': 'password456'
        }, follow_redirects=True)

        assert b'Email already registered.' in response.data