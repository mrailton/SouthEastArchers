from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, verify_csrf
from app.enums import PaymentType
from app.services import payment_processing
from app.services import payments as payment_service
from app.templating import flash, render
from app.utils.checkout_session import clear_session_keys, get_user_id_from_session

router = APIRouter(prefix="/payment", tags=["payment"])


@router.get("/membership", name="payment.membership_payment")
async def membership_payment_page(request: Request, user: CurrentUser):
    return render(request, "payment/membership.html", user=user)


@router.post("/membership", name="payment.membership_payment_post")
async def membership_payment_store(request: Request, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    result = payment_service.initiate_membership_payment(user)
    if result.success:
        data = result.data
        assert data is not None
        request.session["membership_renewal_user_id"] = data["user_id"]
        request.session["membership_renewal_payment_id"] = data["payment_id"]
        request.session["checkout_amount"] = data["amount"]
        request.session["checkout_description"] = data["description"]
        return RedirectResponse(url=f"/payment/checkout/{data['checkout_id']}", status_code=303)

    flash(request, "error", result.message)
    return render(request, "payment/membership.html", user=user, status_code=422)


@router.post("/membership/cash", name="payment.membership_cash_payment")
async def membership_cash_payment(request: Request, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    result = payment_service.initiate_cash_membership_payment(user)
    if result.success:
        data = result.data
        assert data is not None
        return render(
            request,
            "payment/cash_pending.html",
            {
                "payment_type": PaymentType.MEMBERSHIP,
                "amount": data["amount"],
                "instructions": data["instructions"],
            },
            user=user,
        )

    flash(request, "error", result.message)
    return RedirectResponse(url="/payment/membership", status_code=303)


@router.get("/credits", name="payment.credits")
async def credits_payment_page(request: Request, user: CurrentUser):
    if not user.membership:
        flash(request, "error", "You must have an active membership to purchase credits.")
        return RedirectResponse(url="/payment/membership", status_code=303)
    return render(request, "payment/credits.html", user=user)


@router.post("/credits", name="payment.credits_post")
async def credits_payment_store(request: Request, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    try:
        quantity = int(str(raw.get("quantity") or "1"))
    except ValueError, TypeError:
        flash(request, "error", "Invalid quantity.")
        return render(request, "payment/credits.html", user=user, status_code=422)

    quantity_result = payment_service.validate_credit_quantity(quantity)
    if not quantity_result.success:
        flash(request, "error", quantity_result.message)
        return render(request, "payment/credits.html", user=user, status_code=422)

    result = payment_service.initiate_credit_purchase(user, quantity)
    if result.success:
        data = result.data
        assert data is not None
        request.session["credit_purchase_user_id"] = data["user_id"]
        request.session["credit_purchase_payment_id"] = data["payment_id"]
        request.session["credit_purchase_quantity"] = data["quantity"]
        request.session["checkout_amount"] = data["amount"]
        request.session["checkout_description"] = data["description"]
        return RedirectResponse(url=f"/payment/checkout/{data['checkout_id']}", status_code=303)

    flash(request, "error", result.message)
    return render(request, "payment/credits.html", user=user, status_code=422)


@router.post("/credits/cash", name="payment.credits_cash_payment")
async def credits_cash_payment(request: Request, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    try:
        quantity = int(str(raw.get("quantity") or "1"))
    except ValueError, TypeError:
        flash(request, "error", "Invalid quantity.")
        return RedirectResponse(url="/payment/credits", status_code=303)

    quantity_result = payment_service.validate_credit_quantity(quantity)
    if not quantity_result.success:
        flash(request, "error", quantity_result.message)
        return RedirectResponse(url="/payment/credits", status_code=303)

    result = payment_service.initiate_cash_credit_purchase(user, quantity)
    if result.success:
        data = result.data
        assert data is not None
        return render(
            request,
            "payment/cash_pending.html",
            {
                "payment_type": PaymentType.CREDITS,
                "amount": data["amount"],
                "quantity": data["quantity"],
                "instructions": data["instructions"],
            },
            user=user,
        )

    flash(request, "error", result.message)
    return RedirectResponse(url="/payment/credits", status_code=303)


@router.get("/checkout/{checkout_id}", name="payment.show_checkout")
async def show_checkout(checkout_id: str, request: Request, user: CurrentUser):
    amount = request.session.get("checkout_amount", 100.00)
    description = request.session.get("checkout_description", "Payment")
    return render(
        request,
        "payment/checkout.html",
        {"checkout_id": checkout_id, "amount": amount, "description": description},
        user=user,
    )


@router.post("/checkout/{checkout_id}/complete", name="payment.complete_checkout")
async def complete_checkout(checkout_id: str, request: Request, user: CurrentUser):
    raw = await request.form()
    verify_csrf(request, raw.get("csrf_token"))
    result = payment_processing.fulfill_checkout(
        checkout_id=checkout_id,
        session=request.session,
        user_id=get_user_id_from_session(request, user),
    )
    if not result.success:
        flash(request, "error", result.message)
        return RedirectResponse(url=f"/payment/checkout/{checkout_id}", status_code=303)

    fulfillment = result.data
    assert fulfillment is not None
    if fulfillment.session_keys_to_clear:
        clear_session_keys(request, *fulfillment.session_keys_to_clear)
    flash(request, fulfillment.flash_category, fulfillment.flash_message)
    return RedirectResponse(url=fulfillment.redirect_url, status_code=303)


@router.get("/history", name="payment.history")
async def payment_history(request: Request, user: CurrentUser):
    payments = payment_service.get_user_payments(user.id)
    return render(request, "payment/history.html", {"payments": payments}, user=user)
