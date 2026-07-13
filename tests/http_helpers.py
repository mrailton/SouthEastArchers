import re
from types import SimpleNamespace

from starlette.testclient import TestClient


def extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "csrf_token not found in HTML"
    return match.group(1)


class CSRFClient:
    """Wraps TestClient to attach session CSRF tokens to form POSTs automatically."""

    def __init__(self, client: TestClient) -> None:
        self._client = client
        self._csrf: str | None = None

    def _ensure_csrf(self) -> str:
        if self._csrf is not None:
            return self._csrf
        for url in (
            "/auth/login",
            "/auth/signup",
            "/admin/finance/expense/create",
            "/admin/members/create",
            "/admin/dashboard",
            "/",
        ):
            response = self._client.get(url, follow_redirects=True)
            if response.status_code == 200 and "csrf_token" in response.text:
                self._csrf = extract_csrf(response.text)
                return self._csrf
        raise AssertionError("csrf_token not found in any candidate page")

    def get(self, *args, **kwargs):
        return self._client.get(*args, **kwargs)

    def post(self, url: str, data=None, **kwargs):
        if kwargs.get("json") is not None:
            return self._client.post(url, data=data, **kwargs)
        if data is None:
            data = {}
        if isinstance(data, dict) and "csrf_token" not in data:
            data = {**data, "csrf_token": self._ensure_csrf()}
        return self._client.post(url, data=data, **kwargs)

    def __enter__(self):
        self._client.__enter__()
        return self

    def __exit__(self, *args):
        return self._client.__exit__(*args)

    def __getattr__(self, name: str):
        return getattr(self._client, name)


def login(client, email: str, password: str) -> None:
    response = client.get("/auth/login")
    csrf = extract_csrf(response.text)
    if isinstance(client, CSRFClient):
        client._csrf = csrf
    client.post(
        "/auth/login",
        data={"email": email, "password": password, "csrf_token": csrf},
        follow_redirects=False,
    )


def set_session(client, **values) -> None:
    """Set Starlette session keys in tests (requires APP_ENV=testing)."""
    client.post("/__test__/session", json=values)


REDIRECT_STATUS = (302, 303)


def assert_redirect(response, *, location_contains: str | None = None) -> None:
    assert response.status_code in REDIRECT_STATUS, response.status_code
    if location_contains is not None:
        location = response.headers.get("location", "")
        assert location_contains in location, location


def assert_html(response, *needles: str, status_code: int | tuple[int, ...] | None = None) -> None:
    if status_code is not None:
        expected = (status_code,) if isinstance(status_code, int) else status_code
        assert response.status_code in expected, response.status_code
    text = response.text.lower()
    for needle in needles:
        assert needle.lower() in text, f"{needle!r} not in response"


def content_type(response) -> str:
    return response.headers.get("content-type", "")


def email_from_mock(mock_send) -> SimpleNamespace:
    """Build a message-like object from a mocked send_email call."""
    args = mock_send.call_args[0]
    html_body = args[3] if len(args) > 3 else mock_send.call_args.kwargs.get("html_body")
    return SimpleNamespace(
        subject=args[0],
        recipients=list(args[1]),
        body=args[2],
        html=html_body,
    )
