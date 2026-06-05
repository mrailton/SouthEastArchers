from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response

from app.dependencies import CurrentUser, DbSession, require_perms, verify_csrf
from app.forms.admin_forms import ExpenseForm, FinancialStatementForm, IncomeForm
from app.routes.admin._helpers import flash_form_errors
from app.services import finance
from app.templating import flash, render
from app.utils.formdata import request_form_data
from app.utils.pdf import generate_statement_pdf

router = APIRouter(tags=["admin.finance"])


@router.get("/finance", name="admin.finance", dependencies=[require_perms("finance.read")])
async def finance_index(request: Request, db: DbSession, user: CurrentUser):
    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 20))
    if per_page not in (5, 10, 20, 50, 100):
        per_page = 20
    pagination = finance.get_all_transactions_paginated(page=page, per_page=per_page)
    return render(
        request,
        "admin/finance.html",
        {"transactions": pagination.items, "pagination": pagination, "per_page": per_page},
        user=user,
        db=db,
    )


@router.get("/finance/expense/create", name="admin.create_expense", dependencies=[require_perms("finance.create")])
async def create_expense_page(request: Request, db: DbSession, user: CurrentUser):
    form = ExpenseForm()
    return render(request, "admin/create_expense.html", {"form": form}, user=user, db=db)


@router.post("/finance/expense/create", name="admin.create_expense_post", dependencies=[require_perms("finance.create")])
async def create_expense_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = ExpenseForm(formdata=form_data)
    if form.validate():
        result = finance.create_transaction(
            txn_type="expense",
            txn_date=form.date.data,
            amount_cents=int(round(float(form.amount.data) * 100)),
            category=form.category.data,
            description=form.description.data,
            created_by_id=user.id,
            receipt_reference=form.receipt_reference.data or None,
        )
        if result.success:
            flash(request, "success", "Expense recorded successfully!")
            return RedirectResponse(url="/admin/finance", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/create_expense.html", {"form": form}, user=user, db=db, status_code=422)


@router.get("/finance/income/create", name="admin.create_income", dependencies=[require_perms("finance.create")])
async def create_income_page(request: Request, db: DbSession, user: CurrentUser):
    form = IncomeForm()
    return render(request, "admin/create_income.html", {"form": form}, user=user, db=db)


@router.post("/finance/income/create", name="admin.create_income_post", dependencies=[require_perms("finance.create")])
async def create_income_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = IncomeForm(formdata=form_data)
    if form.validate():
        result = finance.create_transaction(
            txn_type="income",
            txn_date=form.date.data,
            amount_cents=int(round(float(form.amount.data) * 100)),
            category=form.category.data,
            description=form.description.data,
            created_by_id=user.id,
            source=form.source.data or None,
        )
        if result.success:
            flash(request, "success", "Income recorded successfully!")
            return RedirectResponse(url="/admin/finance", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, form)
    return render(request, "admin/create_income.html", {"form": form}, user=user, db=db, status_code=422)


@router.get("/finance/statement", name="admin.financial_statement", dependencies=[require_perms("finance.report")])
async def financial_statement_page(request: Request, db: DbSession, user: CurrentUser):
    today = date.today()
    current_year = today.year
    start_date = date(current_year, 3, 1) if today.month >= 3 else date(current_year - 1, 3, 1)
    form = FinancialStatementForm()
    form.start_date.data = start_date
    form.end_date.data = today
    return render(request, "admin/financial_statement.html", {"form": form, "statement": None}, user=user, db=db)


@router.post("/finance/statement", name="admin.financial_statement_post", dependencies=[require_perms("finance.report")])
async def financial_statement_store(request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    form = FinancialStatementForm(formdata=form_data)
    if form.validate():
        if form.end_date.data < form.start_date.data:
            flash(request, "error", "End date must be after start date.")
            return render(request, "admin/financial_statement.html", {"form": form, "statement": None}, user=user, db=db)
        else:
            statement = finance.generate_statement(form.start_date.data, form.end_date.data)
            return render(request, "admin/financial_statement.html", {"form": form, "statement": statement}, user=user, db=db)
    flash_form_errors(request, form)
    return render(request, "admin/financial_statement.html", {"form": form, "statement": None}, user=user, db=db, status_code=422)


@router.get("/finance/statement/pdf", name="admin.financial_statement_pdf", dependencies=[require_perms("finance.report")])
async def financial_statement_pdf(request: Request, db: DbSession, user: CurrentUser):
    start_date_str = request.query_params.get("start_date")
    end_date_str = request.query_params.get("end_date")
    if not start_date_str or not end_date_str:
        flash(request, "error", "Please provide start and end dates.")
        return RedirectResponse(url="/admin/finance/statement", status_code=303)
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        flash(request, "error", "Invalid date format.")
        return RedirectResponse(url="/admin/finance/statement", status_code=303)
    if end_date < start_date:
        flash(request, "error", "End date must be after start date.")
        return RedirectResponse(url="/admin/finance/statement", status_code=303)
    statement = finance.generate_statement(start_date, end_date)
    pdf_bytes = bytes(generate_statement_pdf(statement))
    filename = f"financial_statement_{start_date_str}_to_{end_date_str}.pdf"
    return Response(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/finance/{transaction_id}/edit", name="admin.edit_transaction", dependencies=[require_perms("finance.update")])
async def edit_transaction_page(transaction_id: int, request: Request, db: DbSession, user: CurrentUser):
    transaction = finance.get_transaction_by_id(transaction_id)
    if not transaction:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = ExpenseForm(obj=transaction) if transaction.type == "expense" else IncomeForm(obj=transaction)
    form.amount.data = transaction.amount_cents / 100
    return render(request, "admin/edit_transaction.html", {"transaction": transaction, "form": form}, user=user, db=db)


@router.post("/finance/{transaction_id}/edit", name="admin.edit_transaction_post", dependencies=[require_perms("finance.update")])
async def edit_transaction_store(transaction_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    transaction = finance.get_transaction_by_id(transaction_id)
    if not transaction:
        return render(request, "errors/404.html", user=user, db=db, status_code=404)
    form = ExpenseForm(formdata=form_data, obj=transaction) if transaction.type == "expense" else IncomeForm(formdata=form_data, obj=transaction)
    if form.validate():
        kwargs = {
            "transaction": transaction,
            "txn_date": form.date.data,
            "amount_cents": int(round(float(form.amount.data) * 100)),
            "category": form.category.data,
            "description": form.description.data,
        }
        if transaction.type == "expense":
            kwargs["receipt_reference"] = form.receipt_reference.data or None
        else:
            kwargs["source"] = form.source.data or None
        result = finance.update_transaction(**kwargs)
        if result.success:
            flash(request, "success", "Transaction updated successfully!")
            return RedirectResponse(url="/admin/finance", status_code=303)
        flash(request, "error", result.message or "An error occurred while updating the transaction.")
    flash_form_errors(request, form)
    return render(
        request,
        "admin/edit_transaction.html",
        {"transaction": transaction, "form": form},
        user=user,
        db=db,
        status_code=422,
    )


@router.post("/finance/{transaction_id}/delete", name="admin.delete_transaction", dependencies=[require_perms("finance.delete")])
async def delete_transaction(transaction_id: int, request: Request, db: DbSession, user: CurrentUser):
    form_data = await request_form_data(request)
    verify_csrf(request, form_data.get("csrf_token"))
    result = finance.delete_transaction(transaction_id)
    flash(
        request,
        "success" if result.success else "error",
        result.message or ("Transaction deleted." if result.success else "Error deleting transaction."),
    )
    return RedirectResponse(url="/admin/finance", status_code=303)
