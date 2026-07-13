from starlette.requests import Request

from app.routes.admin._helpers import flash_form_errors, flash_service_warnings, redirect_back, redirect_with_flash
from app.schemas.form_helpers import FormView
from app.services.result import ServiceResult


def _request(**query) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "session": {},
        "query_string": "&".join(f"{k}={v}" for k, v in query.items()).encode(),
    }
    return Request(scope)


def test_redirect_back_uses_default_for_external_url():
    request = _request(next="https://evil.example")
    assert redirect_back(request, "/admin") == "/admin"


def test_redirect_back_uses_relative_next():
    request = _request(next="/admin/members")
    assert redirect_back(request, "/admin") == "/admin/members"


def test_flash_form_errors_from_dict():
    request = _request()
    flash_form_errors(request, {"email": ["Invalid email"]})
    assert ("error", "email: Invalid email") in request.session["_flashes"]


def test_flash_form_errors_from_form_view():
    request = _request()
    form = FormView(errors={"name": ["Too short"]})
    flash_form_errors(request, form)
    assert ("error", "name: Too short") in request.session["_flashes"]


def test_flash_service_warnings():
    request = _request()
    flash_service_warnings(request, ServiceResult.ok(warnings=["Low credits"]))
    assert ("warning", "Warning: Low credits") in request.session["_flashes"]


def test_redirect_with_flash():
    request = _request()
    response = redirect_with_flash(request, "/admin", "success", "Done")
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    assert ("success", "Done") in request.session["_flashes"]
