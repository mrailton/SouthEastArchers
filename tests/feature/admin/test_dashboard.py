"""Admin dashboard routes."""


def test_dashboard_loads_for_admin(admin_client):
    response = admin_client.get("/admin/dashboard")
    assert response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/admin/dashboard", follow_redirects=True)
    assert b"Login" in response.content
