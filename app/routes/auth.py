from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.dependencies import CsrfFormData, CurrentUser, require_guest
from app.schemas.form_helpers import parse_form, single_field_errors
from app.schemas.forms import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignupForm
from app.services import recaptcha as recaptcha_service
from app.services import users
from app.templating import flash, flash_field_errors, render
from app.utils import is_safe_redirect
from app.utils.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", name="auth.login", dependencies=[Depends(require_guest)])
def login_page(request: Request, next_url: str | None = Query(None, alias="next")):
    safe_next = next_url if next_url and is_safe_redirect(next_url) else None
    return render(request, "auth/login.html", {"next_url": safe_next})


@router.post("/login", name="auth.login_post", dependencies=[Depends(require_guest)])
def login_store(
    request: Request,
    form_data: CsrfFormData,
    next_url: str | None = Query(None, alias="next"),
):
    if check_rate_limit(request, "auth:login"):
        flash(request, "error", "Too many login attempts. Please try again later.")
        return render(request, "auth/login.html", status_code=429)

    form, errors, _values = parse_form(LoginForm, form_data)
    if errors:
        flash_field_errors(request, errors)
        return render(request, "auth/login.html", status_code=422)

    assert form is not None
    user = users.authenticate(str(form.email), form.password)
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
    flash(request, "success", "Logged in successfully!")
    destination = next_url if next_url and is_safe_redirect(next_url) else "/member/dashboard"
    return RedirectResponse(url=destination, status_code=303)


@router.get("/signup", name="auth.signup", dependencies=[Depends(require_guest)])
def signup_page(request: Request):
    settings = get_settings()
    return render(request, "auth/signup.html", {"recaptcha_site_key": settings.recaptcha_public_key})


@router.post("/signup", name="auth.signup_post", dependencies=[Depends(require_guest)])
def signup_store(request: Request, form_data: CsrfFormData):
    if check_rate_limit(request, "auth:signup"):
        flash(request, "error", "Too many signup attempts. Please try again later.")
        settings = get_settings()
        return render(request, "auth/signup.html", {"recaptcha_site_key": settings.recaptcha_public_key}, status_code=429)

    settings = get_settings()
    form, errors, form_values = parse_form(SignupForm, form_data)
    if errors:
        flash_field_errors(request, errors)
        return render(
            request,
            "auth/signup.html",
            {
                "errors": single_field_errors(errors),
                "form_values": form_values,
                "recaptcha_site_key": settings.recaptcha_public_key,
            },
            status_code=422,
        )

    assert form is not None
    if not recaptcha_service.verify_recaptcha(form.g_recaptcha_response):
        flash(request, "error", "reCAPTCHA verification failed.")
        return render(
            request,
            "auth/signup.html",
            {"form_values": form_values, "recaptcha_site_key": settings.recaptcha_public_key},
            status_code=422,
        )

    result = users.create_user(
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
def forgot_password_store(request: Request, form_data: CsrfFormData):
    if check_rate_limit(request, "auth:forgot-password"):
        flash(request, "error", "Too many reset requests. Please try again later.")
        return render(request, "auth/forgot_password.html", status_code=429)

    form, errors, _values = parse_form(ForgotPasswordForm, form_data)
    if errors:
        flash_field_errors(request, errors)
        return render(request, "auth/forgot_password.html", status_code=422)

    assert form is not None
    result = users.request_password_reset(str(form.email))
    if not result.success:
        flash(request, "error", result.message)
        return render(request, "auth/forgot_password.html", status_code=422)

    flash(request, "info", "If an account exists with that email, you will receive a password reset link.")
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/reset-password/{token}", name="auth.reset_password", dependencies=[Depends(require_guest)])
def reset_password_page(token: str, request: Request):
    return render(request, "auth/reset_password.html", {"token": token})


@router.post("/reset-password/{token}", name="auth.reset_password_post", dependencies=[Depends(require_guest)])
def reset_password_store(token: str, request: Request, form_data: CsrfFormData):
    if check_rate_limit(request, "auth:reset-password"):
        flash(request, "error", "Too many reset attempts. Please try again later.")
        return render(request, "auth/reset_password.html", {"token": token}, status_code=429)

    user = users.verify_reset_token(token)
    if not user:
        flash(request, "error", "Invalid or expired reset link.")
        return RedirectResponse(url="/auth/forgot-password", status_code=303)

    form, errors, _values = parse_form(ResetPasswordForm, form_data)
    if errors:
        return render(
            request,
            "auth/reset_password.html",
            {"token": token, "errors": single_field_errors(errors)},
            status_code=422,
        )

    assert form is not None
    result = users.reset_password(token, form.password)
    if not result.success:
        flash(request, "error", result.message)
        return RedirectResponse(url="/auth/forgot-password", status_code=303)

    flash(request, "success", f"{result.message} Please login.")
    return RedirectResponse(url="/auth/login", status_code=303)
