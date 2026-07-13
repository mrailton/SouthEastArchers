from app.templating import flash, register_route_names, url_for


def test_url_for_known_route():
    class Route:
        name = "health"
        path = "/health"

    register_route_names([Route()])
    assert url_for("health") == "/health"


def test_url_for_static():
    assert url_for("static", filename="images/logo.png") == "/static/images/logo.png"


def test_url_for_with_params():
    assert url_for("public.news_detail", news_id=5) == "/news/5"


def test_url_for_with_query_params():
    assert url_for("admin.finance", page=2, per_page=25) == "/admin/finance?page=2&per_page=25"


def test_flash_stores_message():
    from starlette.requests import Request

    scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "session": {}}
    request = Request(scope)
    flash(request, "success", "Saved")
    assert request.session["_flashes"] == [("success", "Saved")]


def test_url_for_unknown_route_raises():
    import pytest

    with pytest.raises(ValueError, match="Unknown route"):
        url_for("definitely.not.a.route")


def test_anonymous_user_permissions():
    from app.templating import AnonymousUser

    user = AnonymousUser()
    assert user.is_authenticated is False
    assert user.has_permission("members.read") is False
    assert user.has_any_permission("members.read", "finance.read") is False


def test_url_for_external():
    assert url_for("health", _external=True).startswith("http")
