from app import db
from app.models import User
from tests.conftest import login


class TestMember:
    def test_dashboard(self, client, regular_user):
        login(client, 'user@test.com', 'user123')
        response = client.get('/member/dashboard')
        assert response.status_code == 200

    def test_profile(self, client, regular_user):
        login(client, 'user@test.com', 'user123')
        response = client.get('/member/profile')
        assert response.status_code == 200

    def test_purchase_credits(self, client, regular_user):
        """Test member can purchase credits."""
        login(client, 'user@test.com', 'user123')

        response = client.get('/member/credits/purchase')
        assert response.status_code == 200

        user = db.session.get(User, regular_user.id)
        initial_credits = user.current_membership.credits_remaining

        response = client.post('/member/credits/purchase', data={
            'credits': 5
        }, follow_redirects=True)

        assert response.status_code == 200
        user = db.session.get(User, regular_user.id)
        assert user.current_membership.credits_remaining == initial_credits + 5


    def test_purchase_credits_no_membership(self, client, app):
        # Create user without membership
        user = User(email='nomembership@test.com', name='No Membership')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        login(client, 'nomembership@test.com', 'password123')

        response = client.post('/member/credits/purchase', data={
            'credits': 10
        }, follow_redirects=True)

        # Should handle gracefully (membership is None)
        assert response.status_code == 200
