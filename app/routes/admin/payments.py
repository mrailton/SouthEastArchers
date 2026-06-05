from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CsrfFormData, CurrentUser, require_perms
from app.services import payment_processing, payments
from app.services.result import ErrorCode
from app.templating import flash, render

router = APIRouter(tags=["admin.payments"])


@router.get("/payments", name="admin.pending_payments", dependencies=[require_perms("payments.approve")])
def pending_payments(request: Request, user: CurrentUser):
    payment_rows = payments.get_pending_cash_payment_rows()
    return render(request, "admin/pending_payments.html", {"payment_data": payment_rows}, user=user)


@router.post("/payments/{payment_id}/approve", name="admin.approve_payment", dependencies=[require_perms("payments.approve")])
def approve_payment(payment_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    redirect_to = form_data.get("redirect_to") or "/admin/payments"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments"

    result = payments.approve_cash_payment(payment_id)
    if result.error_code == ErrorCode.NOT_FOUND:
        return render(request, "errors/404.html", user=user, status_code=404)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=redirect_to, status_code=303)


@router.get("/payments/reconcile", name="admin.reconcile_payments", dependencies=[require_perms("payments.approve")])
def reconcile_payments_page(request: Request, user: CurrentUser):
    payment_rows = payments.get_unfulfilled_online_payment_rows()
    return render(request, "admin/reconcile_payments.html", {"payment_data": payment_rows}, user=user)


def _replay_payment_side_effects_response(
    payment_id: int,
    request: Request,
    user: CurrentUser,
    *,
    redirect_to: str,
    send_mail: bool,
):
    result = payments.replay_completed_payment_side_effects(payment_id, send_mail=send_mail)
    if result.error_code == ErrorCode.NOT_FOUND:
        return render(request, "errors/404.html", user=user, status_code=404)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=redirect_to, status_code=303)


@router.post(
    "/payments/replay-side-effects",
    name="admin.replay_payment_side_effects",
    dependencies=[require_perms("payments.approve")],
)
def replay_payment_side_effects_form(request: Request, user: CurrentUser, form_data: CsrfFormData):
    redirect_to = form_data.get("redirect_to") or "/admin/payments/reconcile"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments/reconcile"

    raw_id = form_data.get("payment_id")
    try:
        payment_id = int(raw_id) if raw_id is not None else 0
    except TypeError, ValueError:
        payment_id = 0
    if payment_id < 1:
        flash(request, "error", "Enter a valid payment ID.")
        return RedirectResponse(url=redirect_to, status_code=303)

    send_mail = form_data.get("send_mail", "1") != "0"
    return _replay_payment_side_effects_response(
        payment_id,
        request,
        user,
        redirect_to=redirect_to,
        send_mail=send_mail,
    )


@router.post(
    "/payments/{payment_id}/replay-side-effects",
    name="admin.replay_payment_side_effects_by_id",
    dependencies=[require_perms("payments.approve")],
)
def replay_payment_side_effects(payment_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    redirect_to = form_data.get("redirect_to") or "/admin/payments/reconcile"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments/reconcile"
    send_mail = form_data.get("send_mail", "1") != "0"
    return _replay_payment_side_effects_response(
        payment_id,
        request,
        user,
        redirect_to=redirect_to,
        send_mail=send_mail,
    )


@router.post(
    "/payments/{payment_id}/reconcile",
    name="admin.reconcile_payment",
    dependencies=[require_perms("payments.approve")],
)
def reconcile_payment(payment_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    redirect_to = form_data.get("redirect_to") or "/admin/payments/reconcile"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments/reconcile"

    result = payment_processing.reconcile_sumup_payment(payment_id)
    if result.error_code == ErrorCode.NOT_FOUND:
        return render(request, "errors/404.html", user=user, status_code=404)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=redirect_to, status_code=303)


@router.post("/payments/{payment_id}/reject", name="admin.reject_payment", dependencies=[require_perms("payments.approve")])
def reject_payment(payment_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    redirect_to = form_data.get("redirect_to") or "/admin/payments"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments"

    result = payments.reject_cash_payment(payment_id)
    if result.error_code == ErrorCode.NOT_FOUND:
        return render(request, "errors/404.html", user=user, status_code=404)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=redirect_to, status_code=303)
