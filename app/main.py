import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.db import init_db
from app.exceptions import AlreadyAuthenticated, AuthorizationError, CsrfError, LoginRequired
from app.routes import api_router
from app.templating import AnonymousUser, register_route_names, render, setup_template_globals

logger = logging.getLogger(__name__)
settings = get_settings()
init_db(settings)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "resources" / "static"
BUILT_ASSETS_DIR = STATIC_DIR / "dist" / "assets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.events.handlers import connect_handlers

    register_route_names(list(app.routes))
    connect_handlers()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age_seconds,
    https_only=settings.session_secure_cookie,
    same_site=settings.session_same_site,
)

# Built bundle first (more specific path), then raw files (images, etc.)
if BUILT_ASSETS_DIR.is_dir():
    app.mount("/static/assets", StaticFiles(directory=str(BUILT_ASSETS_DIR)), name="static-built")
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

setup_template_globals()
app.include_router(api_router)


@app.middleware("http")
async def run_deferred_event_handlers(request: Request, call_next):
    from app.events.background import run_handler_safe, take_deferred_handlers

    response = await call_next(request)
    deferred = take_deferred_handlers()
    if settings.is_testing:
        for handler, args, kwargs in deferred:
            run_handler_safe(handler, *args, **kwargs)
    else:
        for handler, args, kwargs in deferred:
            asyncio.create_task(asyncio.to_thread(run_handler_safe, handler, *args, **kwargs))
    return response


def _session_user(request: Request):
    from app.services import users

    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return users.get_session_user_by_id(int(user_id))


def _session_user_for_error_page(request: Request):
    """Load the current user for error templates; never raise on DB failure."""
    try:
        user = _session_user(request)
    except Exception:
        logger.warning("Could not load session user for error page", exc_info=True)
        return AnonymousUser()
    return user if user is not None else AnonymousUser()


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, _exc: LoginRequired):
    next_url = request.url.path
    if request.url.query:
        next_url = f"{next_url}?{request.url.query}"
    return RedirectResponse(url=f"/auth/login?next={quote(next_url)}", status_code=303)


@app.exception_handler(AlreadyAuthenticated)
async def already_authenticated_handler(request: Request, _exc: AlreadyAuthenticated):
    return RedirectResponse(url="/member/dashboard", status_code=303)


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, _exc: AuthorizationError):
    user = _session_user_for_error_page(request)
    return render(request, "errors/403.html", status_code=403, user=user)


@app.exception_handler(CsrfError)
async def csrf_error_handler(request: Request, _exc: CsrfError):
    user = _session_user_for_error_page(request)
    return render(request, "errors/csrf.html", status_code=403, user=user)


@app.exception_handler(404)
async def not_found_handler(request: Request, _exc: StarletteHTTPException):
    user = _session_user_for_error_page(request)
    return render(request, "errors/404.html", status_code=404, user=user)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing %s", request.url.path)
    user = _session_user_for_error_page(request)
    return render(request, "errors/500.html", status_code=500, user=user)


if settings.is_testing:

    @app.post("/__test__/session")
    async def set_test_session(request: Request):
        data = await request.json()
        for key, value in data.items():
            request.session[key] = value
        return {"ok": True}
