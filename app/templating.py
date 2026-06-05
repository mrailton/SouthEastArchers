from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode, urljoin

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.dependencies import get_csrf_token
from app.routes_map import FALLBACK_ROUTES
from app.services import settings as app_settings

TEMPLATES_DIR = Path(__file__).parent / "resources" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_route_names: dict[str, str] = dict(FALLBACK_ROUTES)


class AnonymousUser:
    is_authenticated = False
    membership = None

    @staticmethod
    def has_permission(_permission_name: str) -> bool:
        return False

    @staticmethod
    def has_any_permission(*_permission_names: str) -> bool:
        return False


def register_route_names(routes: list) -> None:
    for route in routes:
        name = getattr(route, "name", None)
        path = getattr(route, "path", None)
        if name and path:
            _route_names[name] = path


def url_for(name: str, _external: bool = False, **path_params: object) -> str:
    if name == "static":
        filename = str(path_params.get("filename", ""))
        path = f"/static/{filename}"
    else:
        route_path = _route_names.get(name)
        if route_path is None:
            raise ValueError(f"Unknown route name: {name}")
        path = route_path
        used_keys: set[str] = set()
        for key, value in path_params.items():
            if key.startswith("_"):
                continue
            placeholder = "{" + key + "}"
            if placeholder in path:
                path = path.replace(placeholder, str(value))
                used_keys.add(key)
        query_params = {k: v for k, v in path_params.items() if k not in used_keys and not k.startswith("_")}
        if query_params:
            path = f"{path}?{urlencode(query_params)}"

    if _external:
        return urljoin(get_settings().app_url.rstrip("/") + "/", path.lstrip("/"))
    return path


def get_flashed_messages(with_categories: bool = False) -> list:
    # Populated per-request in render(); kept for Jinja signature compatibility.
    return []


def flash(request: Request, category: str, message: str) -> None:
    flashes: list[tuple[str, str]] = request.session.get("_flashes", [])
    flashes.append((category, message))
    request.session["_flashes"] = flashes


def flash_field_errors(request: Request, errors: dict[str, list[str]]) -> None:
    from app.schemas.form_helpers import single_field_errors

    for message in single_field_errors(errors).values():
        flash(request, "error", message)


def _feature_flags() -> dict[str, bool]:
    return {
        "news_enabled": app_settings.get("news_enabled"),
        "events_enabled": app_settings.get("events_enabled"),
    }


def _pop_flashes(request: Request) -> list[tuple[str, str]]:
    flashes: list[tuple[str, str]] = request.session.pop("_flashes", [])
    return flashes


def endpoint_is(request: Request, names: str | list[str]) -> bool:
    route_name = getattr(request.scope.get("route"), "name", "") or ""
    if isinstance(names, str):
        return route_name == names
    return route_name in names


def setup_template_globals() -> None:
    templates.env.globals.update(
        {
            "url_for": url_for,
            "get_flashed_messages": get_flashed_messages,
            "endpoint_is": endpoint_is,
        }
    )


def render(
    request: Request,
    name: str,
    context: dict | None = None,
    user=None,
    status_code: int = 200,
):
    current_user = user if user is not None else AnonymousUser()
    flashes = _pop_flashes(request)
    templates.env.globals["get_flashed_messages"] = lambda with_categories=False: flashes

    ctx: dict = {
        "request": request,
        "csrf_token": get_csrf_token(request),
        "current_user": current_user,
        "user": current_user,
        "errors": {},
        "now": datetime.now(UTC),
        "endpoint_is": endpoint_is,
        **_feature_flags(),
    }
    if "validation_errors" in request.session:
        ctx["errors"] = request.session.pop("validation_errors")
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
