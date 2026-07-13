import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.db import db, init_db, reset_current_session, set_current_session
from app.db.session import has_current_session
from app.exceptions import AlreadyAuthenticated, AuthorizationError, CsrfError, LoginRequired
from app.routes import api_router
from app.templating import AnonymousUser, register_route_names, render, setup_template_globals

logger = logging.getLogger(__name__)
settings = get_settings()
init_db(settings)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "resources" / "static"
BUILT_ASSETS_DIR = STATIC_DIR / "dist" / "assets"


def _configure_app_logging() -> None:
    """Attach a StreamHandler to the 'app' logger hierarchy.

    Uvicorn only wires up handlers for its own loggers; without this, every
    app.* logger propagates to the root logger which has no handlers, and all
    messages are silently dropped.  We add our own handler directly so the
    level set via LOG_LEVEL is actually honoured.

    In the test environment we only set the level — pytest's caplog fixture
    captures via propagation and adding a handler here would break that.
    """
    app_logger = logging.getLogger("app")
    app_logger.setLevel(settings.log_level.upper())
    if not settings.is_testing and not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)-8s  %(name)s - %(message)s"))
        app_logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.events.handlers import connect_handlers

    _configure_app_logging()
    register_route_names(list(app.routes))
    connect_handlers()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
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


@contextmanager
def _error_page_db_session():
    """Ensure an active DB session for error-page rendering.

    Exception handlers run outside FastAPI's dependency injection lifecycle,
    so they have no session when a route never matched (e.g. 404 on /favicon.ico)
    or after get_db() has already been torn down.  Open a fresh read session
    only when one is not already present; always close it afterwards.
    """
    if has_current_session():
        yield
        return

    session = db.create_session()
    token = set_current_session(session)
    try:
        yield
    finally:
        session.close()
        reset_current_session(token)


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
    with _error_page_db_session():
        user = _session_user_for_error_page(request)
        return render(request, "errors/403.html", status_code=403, user=user)


@app.exception_handler(CsrfError)
async def csrf_error_handler(request: Request, _exc: CsrfError):
    with _error_page_db_session():
        user = _session_user_for_error_page(request)
        return render(request, "errors/csrf.html", status_code=403, user=user)


@app.exception_handler(404)
async def not_found_handler(request: Request, _exc: StarletteHTTPException):
    with _error_page_db_session():
        user = _session_user_for_error_page(request)
        return render(request, "errors/404.html", status_code=404, user=user)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing %s", request.url.path)
    with _error_page_db_session():
        user = _session_user_for_error_page(request)
        return render(request, "errors/500.html", status_code=500, user=user)


if settings.is_testing:

    @app.post("/__test__/session")
    async def set_test_session(request: Request):
        data = await request.json()
        for key, value in data.items():
            request.session[key] = value
        return {"ok": True}
