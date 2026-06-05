from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.services import payments
from app.templating import flash, render
from app.utils.formdata import request_form_data

router = APIRouter(tags=["admin.payments"])


@router.get("/payments", name="admin.pending_payments", dependencies=[require_perms("payments.approve")])
async def pending_payments(request: Request, db: DbSession, user: CurrentUser):
    payment_rows = payments.get_pending_cash_payment_rows()
    return render(request, "admin/pending_payments.html", {"payment_data": payment_rows}, user=user)


@router.post("/payments/{payment_id}/approve", name="admin.approve_payment", dependencies=[require_perms("payments.approve")])
async def approve_payment(payment_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    redirect_to = form_data.get("redirect_to") or "/admin/payments"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments"

    result = payments.approve_cash_payment(payment_id)
    if result.message == "Payment not found.":
        return render(request, "errors/404.html", user=user, status_code=404)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=redirect_to, status_code=303)


@router.post("/payments/{payment_id}/reject", name="admin.reject_payment", dependencies=[require_perms("payments.approve")])
async def reject_payment(payment_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    redirect_to = form_data.get("redirect_to") or "/admin/payments"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments"

    result = payments.reject_cash_payment(payment_id)
    if result.message == "Payment not found.":
        return render(request, "errors/404.html", user=user, status_code=404)
    flash(request, "success" if result.success else "error", result.message)
    return RedirectResponse(url=redirect_to, status_code=303)
