"""Tests for decorators"""

from app.utils.decorators import any_permission_required


def test_redirects_when_not_logged_in_member_dashboard(client):
    """Test that login_required redirects to login when not authenticated"""
    response = client.get("/member/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_allows_access_when_logged_in(client, test_user):
    """Test that login_required allows access when authenticated"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/member/dashboard")
    assert response.status_code == 200


def test_admin_redirects_when_not_logged_in(client):
    """Test that admin_required redirects when not authenticated"""
    response = client.get("/admin/dashboard")
    assert response.status_code == 302


def test_admin_redirects_when_not_admin(client, test_user):
    """Test that admin_required redirects when user is not admin"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/dashboard")
    assert response.status_code in [302, 403]


def test_admin_allows_access_for_admin(client, admin_user):
    """Test that admin_required allows access for admin users"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/dashboard")
    assert response.status_code == 200


def test_permission_required_no_permission(client, test_user):
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})
    # test_user has no permissions by default
    response = client.get("/admin/roles")
    assert response.status_code == 403


def test_any_permission_required(app, admin_user):
    from unittest.mock import patch

    from flask import Flask
    from flask_login import LoginManager

    # Create a minimal app for testing the decorator in isolation
    test_app = Flask(__name__)
    test_app.config["SECRET_KEY"] = "test"
    test_app.config["WTF_CSRF_ENABLED"] = False

    login_manager = LoginManager(test_app)

    @login_manager.user_loader
    def load_user(user_id):
        return admin_user

    @test_app.route("/any")
    @any_permission_required(["p1", "p2"])
    def any_route():
        return "OK"

    @test_app.route("/login", endpoint="auth.login")
    def login_mock():
        return "Login Page"

    # 1. Test Unauthenticated
    with test_app.test_client() as client:
        response = client.get("/any")
        assert response.status_code == 302

    # For the authenticated tests, we mock current_user
    # Using patch directly on the module where it's imported
    with patch("app.utils.decorators.current_user") as mock_user:
        mock_user.is_authenticated = True

        # 2. Test Authenticated but no permission
        with test_app.test_client() as client:
            # Manually implement the check that the decorator does
            # We want current_user.has_any_permission(*perms) to return False
            mock_user.has_any_permission.return_value = False
            # Ensure it's not an AsyncMock
            from unittest.mock import MagicMock

            mock_user.has_any_permission = MagicMock(return_value=False)

            response = client.get("/any")
            assert response.status_code == 403

        # 3. Test Authenticated with permission
        with test_app.test_client() as client:
            mock_user.has_any_permission = MagicMock(return_value=True)
            response = client.get("/any")
            assert response.status_code == 200
            assert response.data == b"OK"
