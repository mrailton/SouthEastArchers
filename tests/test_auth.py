from tests.conftest import login


class TestAuthentication:
    def test_successful_login(self, client, regular_user):
        response = client.get('/auth/login')
        assert response.status_code == 200

        response = login(client, 'user@test.com', 'user123')
        assert response.status_code == 200


    def test_login_with_redirect(self, client, regular_user):
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'user123'
        }, query_string={'next': '/member/dashboard'}, follow_redirects=True)

        assert response.status_code == 200

    def test_login_invalid_credentials(self, client, regular_user):
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_when_authenticated(self, client, regular_user):
        login(client, 'user@test.com', 'user123')
        response = client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200

    def test_register_when_authenticated(self, client, regular_user):
        login(client, 'user@test.com', 'user123')
        response = client.get('/auth/register', follow_redirects=True)
        assert response.status_code == 200

    def test_logout(self, client, regular_user):
        login(client, 'user@test.com', 'user123')
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200