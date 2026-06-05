import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.database import mark_for_commit
from app.dependencies import CurrentUser, DbSession, require_guest, verify_csrf
from app.events import password_reset_requested, user_registered
from app.schemas.forms import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignupForm
from app.services import recaptcha as recaptcha_service
from app.services import users as user_service
from app.templating import flash, render

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _validation_errors(exc: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        errors[field or "form"] = error["msg"]
    return errors


def _flash_validation_errors(request: Request, exc: ValidationError) -> None:
    for message in _validation_errors(exc).values():
        flash(request, "error", message)


@router.get("/login", name="auth.login", dependencies=[Depends(require_guest)])
def login_page(request: Request):
    return render(request, "auth/login.html")


@router.post("/login", name="auth.login_post", dependencies=[Depends(require_guest)])
async def login_store(
    request: Request,
    db: DbSession,
    next_url: str | None = Query(None, alias="next"),
):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    try:
        form = LoginForm(
            csrf_token=str(raw.get("csrf_token", "")),
            email=str(raw.get("email", "")),
            password=str(raw.get("password", "")),
        )
    except ValidationError as exc:
        _flash_validation_errors(request, exc)
        return render(request, "auth/login.html", status_code=422)

    user = user_service.authenticate(db, str(form.email), form.password)
    if user is None:
        flash(request, "error", "Invalid username or password.")
        return render(request, "auth/login.html", status_code=422)
    if not user.is_active:
        flash(request, "error", "Your account is not currently active.")
        return render(request, "auth/login.html", status_code=422)

    csrf_token = request.session.get("csrf_token")
    request.session.clear()
    request.session["user_id"] = user.id
    if csrf_token:
        request.session["csrf_token"] = csrf_token
    mark_for_commit(db)
    flash(request, "success", "Logged in successfully!")
    destination = next_url if next_url and next_url.startswith("/") else "/member/dashboard"
    return RedirectResponse(url=destination, status_code=303)


@router.get("/signup", name="auth.signup", dependencies=[Depends(require_guest)])
def signup_page(request: Request):
    settings = get_settings()
    return render(request, "auth/signup.html", {"recaptcha_site_key": settings.recaptcha_public_key})


@router.post("/signup", name="auth.signup_post", dependencies=[Depends(require_guest)])
async def signup_store(request: Request, db: DbSession):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    form_values = {key: str(raw.get(key, "")) for key in raw.keys()}
    settings = get_settings()
    try:
        form = SignupForm(
            csrf_token=str(raw.get("csrf_token", "")),
            name=str(raw.get("name", "")),
            email=str(raw.get("email", "")),
            phone=str(raw.get("phone", "")),
            password=str(raw.get("password", "")),
            password_confirm=str(raw.get("password_confirm", "")),
            qualification=str(raw.get("qualification", "none")),
            qualification_detail=str(raw.get("qualification_detail", "")),
            g_recaptcha_response=str(raw.get("g-recaptcha-response", "")),
        )
    except ValidationError as exc:
        _flash_validation_errors(request, exc)
        return render(
            request,
            "auth/signup.html",
            {
                "errors": _validation_errors(exc),
                "form_values": form_values,
                "recaptcha_site_key": settings.recaptcha_public_key,
            },
            status_code=422,
        )

    if not await recaptcha_service.verify_recaptcha(form.g_recaptcha_response):
        flash(request, "error", "reCAPTCHA verification failed.")
        return render(
            request,
            "auth/signup.html",
            {"form_values": form_values, "recaptcha_site_key": settings.recaptcha_public_key},
            status_code=422,
        )

    result = user_service.create_user(
        db,
        name=form.name,
        email=str(form.email),
        password=form.password,
        phone=form.phone or None,
        qualification=form.qualification,
        qualification_detail=form.qualification_detail or None,
    )
    if not result.success:
        flash(request, "error", result.message)
        return render(
            request,
            "auth/signup.html",
            {"form_values": form_values, "recaptcha_site_key": settings.recaptcha_public_key},
            status_code=422,
        )

    user = result.data
    assert user is not None
    mark_for_commit(db)
    try:
        user_registered.send(user_id=user.id)
    except Exception:
        logger.exception("Failed to dispatch user_registered event")

    flash(
        request,
        "success",
        "Thank you for signing up. A coach will review your information shortly and get back to you to discuss membership.",
    )
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/logout", name="auth.logout")
def logout(request: Request, _user: CurrentUser):
    request.session.clear()
    flash(request, "success", "Logged out successfully!")
    return RedirectResponse(url="/", status_code=303)


@router.get("/forgot-password", name="auth.forgot_password", dependencies=[Depends(require_guest)])
def forgot_password_page(request: Request):
    return render(request, "auth/forgot_password.html")


@router.post("/forgot-password", name="auth.forgot_password_post", dependencies=[Depends(require_guest)])
async def forgot_password_store(request: Request, db: DbSession):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    try:
        form = ForgotPasswordForm(
            csrf_token=str(raw.get("csrf_token", "")),
            email=str(raw.get("email", "")),
        )
    except ValidationError as exc:
        _flash_validation_errors(request, exc)
        return render(request, "auth/forgot_password.html", status_code=422)

    user = user_service.get_user_by_email(db, str(form.email))
    if user:
        token = user_service.generate_reset_token(user.email)
        try:
            password_reset_requested.send(user_id=user.id, token=token)
        except Exception:
            logger.exception("Failed to send password reset email to %s", user.email)
            flash(request, "error", "An error occurred sending the email. Please try again later.")
            return render(request, "auth/forgot_password.html", status_code=422)

    flash(request, "info", "If an account exists with that email, you will receive a password reset link.")
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/reset-password/{token}", name="auth.reset_password", dependencies=[Depends(require_guest)])
def reset_password_page(token: str, request: Request):
    return render(request, "auth/reset_password.html", {"token": token})


@router.post("/reset-password/{token}", name="auth.reset_password_post", dependencies=[Depends(require_guest)])
async def reset_password_store(token: str, request: Request, db: DbSession):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    user = user_service.verify_reset_token(db, token)
    if not user:
        flash(request, "error", "Invalid or expired reset link.")
        return RedirectResponse(url="/auth/forgot-password", status_code=303)

    try:
        form = ResetPasswordForm(
            csrf_token=str(raw.get("csrf_token", "")),
            password=str(raw.get("password", "")),
            password_confirm=str(raw.get("password_confirm", "")),
        )
    except ValidationError as exc:
        return render(
            request,
            "auth/reset_password.html",
            {"token": token, "errors": _validation_errors(exc)},
            status_code=422,
        )

    result = user_service.reset_password(db, token, form.password)
    if not result.success:
        flash(request, "error", result.message)
        return RedirectResponse(url="/auth/forgot-password", status_code=303)

    mark_for_commit(db)
    flash(request, "success", f"{result.message} Please login.")
    return RedirectResponse(url="/auth/login", status_code=303)
