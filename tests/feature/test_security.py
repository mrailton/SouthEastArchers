from app.utils import rate_limit


def test_csrf_mismatch_returns_403(client):
    response = client.post(
        "/auth/login",
        data={"email": "test@example.com", "password": "password", "csrf_token": "invalid"},
    )
    assert response.status_code == 403


def test_login_rate_limit_returns_429(client):
    rate_limit.clear_rate_limits()
    for _ in range(10):
        client.post(
            "/auth/login",
            data={"email": "nobody@example.com", "password": "wrong"},
        )
    response = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "wrong"},
    )
    assert response.status_code == 429


def test_admin_payment_not_found_uses_error_code(admin_client):
    response = admin_client.post(
        "/admin/payments/999999/approve",
        data={"redirect_to": "/admin/payments"},
        follow_redirects=False,
    )
    assert response.status_code == 404
