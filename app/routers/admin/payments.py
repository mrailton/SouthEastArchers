from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, verify_csrf
from app.enums import PaymentMethod, PaymentType
from app.events import credit_purchased, payment_completed
from app.utils.formdata import request_form_data
from app.models import Credit, Membership
from app.repositories import CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.routers.admin._helpers import require_perms
from app.services.settings_service import SettingsService
from app.templating import flash, render

router = APIRouter(tags=["admin.payments"])


@router.get("/payments", name="admin.pending_payments", dependencies=[require_perms("payments.approve")])
async def pending_payments(request: Request, db: DbSession, user: CurrentUser):
    payments = PaymentRepository.get_pending_cash()
    payment_rows = [{"payment": p, "user": UserRepository.get_by_id(p.user_id)} for p in payments]
    return render(request, "admin/pending_payments.html", {"payment_data": payment_rows}, user=user, db=db)


@router.post("/payments/{payment_id}/approve", name="admin.approve_payment", dependencies=[require_perms("payments.approve")])
async def approve_payment(payment_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    redirect_to = form_data.get("redirect_to") or "/admin/payments"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments"

    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
        flash(request, "error", "This payment cannot be approved.")
        return RedirectResponse(url=redirect_to, status_code=303)

    member = UserRepository.get_by_id(payment.user_id)
    if not member:
        flash(request, "error", "User not found.")
        return RedirectResponse(url=redirect_to, status_code=303)

    try:
        payment.mark_completed(processor="cash")
        if payment.payment_type == PaymentType.MEMBERSHIP:
            if member.membership:
                if member.membership.status != "active":
                    member.membership.activate()
                else:
                    expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                    member.membership.renew(expiry_date=expiry_date)
            else:
                expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                membership = Membership(
                    user_id=member.id,
                    start_date=date.today(),
                    expiry_date=expiry_date,
                    initial_credits=SettingsService.get("membership_shoots_included"),
                    purchased_credits=0,
                    status="active",
                )
                MembershipRepository.add(membership)
        elif payment.payment_type == PaymentType.CREDITS:
            quantity = 1
            description = payment.description or ""
            if "shooting credits" in description.lower():
                try:
                    quantity = int(description.split()[0])
                except (ValueError, IndexError):
                    quantity = 1
            if member.membership:
                member.membership.add_credits(quantity)
            CreditRepository.add(Credit(user_id=member.id, amount=quantity, payment_id=payment.id))

        PaymentRepository.save()
        try:
            if payment.payment_type == PaymentType.CREDITS:
                quantity = 1
                if "shooting credits" in (payment.description or "").lower():
                    try:
                        quantity = int(payment.description.split()[0])
                    except (ValueError, IndexError):
                        quantity = 1
                credit_purchased.send(user_id=member.id, payment_id=payment.id, quantity=quantity)
            else:
                payment_completed.send(user_id=member.id, payment_id=payment.id, payment_type=payment.payment_type)
        except Exception:
            pass
        flash(request, "success", f"Payment approved for {member.name}!")
    except Exception as exc:
        flash(request, "error", f"Error approving payment: {exc}")

    return RedirectResponse(url=redirect_to, status_code=303)


@router.post("/payments/{payment_id}/reject", name="admin.reject_payment", dependencies=[require_perms("payments.approve")])
async def reject_payment(payment_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    redirect_to = form_data.get("redirect_to") or "/admin/payments"
    if not redirect_to.startswith("/"):
        redirect_to = "/admin/payments"

    payment = PaymentRepository.get_by_id(payment_id)
    if not payment:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
        flash(request, "error", "This payment cannot be rejected.")
        return RedirectResponse(url=redirect_to, status_code=303)
    member = UserRepository.get_by_id(payment.user_id)
    payment.status = "cancelled"
    PaymentRepository.save()
    flash(request, "success", f"Payment rejected for {member.name if member else 'user'}.")

    return RedirectResponse(url=redirect_to, status_code=303)
