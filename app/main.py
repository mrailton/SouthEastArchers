from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.db import init_db
from app.dependencies import LoginRequired
from app.policies import AuthorizationError
from app.routers import api_router
from app.templating import register_route_names, render, setup_template_globals

settings = get_settings()
init_db(settings)

STATIC_DIR = Path(__file__).resolve().parent.parent / "resources" / "static"


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
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

setup_template_globals()
app.include_router(api_router)


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, _exc: LoginRequired):
    next_url = request.url.path
    if request.url.query:
        next_url = f"{next_url}?{request.url.query}"
    return RedirectResponse(url=f"/auth/login?next={quote(next_url)}", status_code=303)


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, _exc: AuthorizationError):
    return render(request, "errors/403.html", status_code=403)


if settings.is_testing:
    @app.post("/__test__/session")
    async def set_test_session(request: Request):
        data = await request.json()
        for key, value in data.items():
            request.session[key] = value
        return {"ok": True}
