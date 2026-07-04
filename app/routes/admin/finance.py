from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response

from app.dependencies import CsrfFormData, CurrentUser, require_perms
from app.routes.admin._helpers import flash_form_errors
from app.schemas.admin_forms import (
    EXPENSE_CATEGORY_CHOICES,
    INCOME_CATEGORY_CHOICES,
    ExpenseForm,
    FinancialStatementForm,
    IncomeForm,
)
from app.schemas.form_helpers import FormView, parse_form
from app.services import finance
from app.services.settings import get_membership_year_start
from app.templating import flash, render
from app.utils.pdf import generate_statement_pdf

router = APIRouter(tags=["admin.finance"])


def _expense_form_view(*, values: dict | None = None, errors: dict | None = None) -> FormView:
    return FormView(values=values or {}, errors=errors, choices={"category": EXPENSE_CATEGORY_CHOICES})


def _income_form_view(*, values: dict | None = None, errors: dict | None = None) -> FormView:
    return FormView(values=values or {}, errors=errors, choices={"category": INCOME_CATEGORY_CHOICES})


def _statement_form_view(*, values: dict | None = None, errors: dict | None = None) -> FormView:
    return FormView(values=values or {}, errors=errors)


def _transaction_form_view(transaction, *, values: dict | None = None, errors: dict | None = None) -> FormView:
    choices = EXPENSE_CATEGORY_CHOICES if transaction.type == "expense" else INCOME_CATEGORY_CHOICES
    return FormView(values=values or {}, errors=errors, choices={"category": choices})


@router.get("/finance", name="admin.finance", dependencies=[require_perms("finance.read")])
def finance_index(request: Request, user: CurrentUser):
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
    )


@router.get("/finance/expense/create", name="admin.create_expense", dependencies=[require_perms("finance.create")])
def create_expense_page(request: Request, user: CurrentUser):
    form = _expense_form_view()
    return render(request, "admin/create_expense.html", {"form": form}, user=user)


@router.post("/finance/expense/create", name="admin.create_expense_post", dependencies=[require_perms("finance.create")])
def create_expense_store(request: Request, user: CurrentUser, form_data: CsrfFormData):
    parsed, errors, values = parse_form(ExpenseForm, form_data)
    form = _expense_form_view(values=values, errors=errors)
    if parsed:
        result = finance.create_transaction(
            txn_type="expense",
            txn_date=parsed.date,
            amount_cents=int(round(float(parsed.amount) * 100)),
            category=parsed.category,
            description=parsed.description,
            created_by_id=user.id,
            receipt_reference=parsed.receipt_reference or None,
        )
        if result.success:
            flash(request, "success", "Expense recorded successfully!")
            return RedirectResponse(url="/admin/finance", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, errors)
    return render(request, "admin/create_expense.html", {"form": form}, user=user, status_code=422)


@router.get("/finance/income/create", name="admin.create_income", dependencies=[require_perms("finance.create")])
def create_income_page(request: Request, user: CurrentUser):
    form = _income_form_view()
    return render(request, "admin/create_income.html", {"form": form}, user=user)


@router.post("/finance/income/create", name="admin.create_income_post", dependencies=[require_perms("finance.create")])
def create_income_store(request: Request, user: CurrentUser, form_data: CsrfFormData):
    parsed, errors, values = parse_form(IncomeForm, form_data)
    form = _income_form_view(values=values, errors=errors)
    if parsed:
        result = finance.create_transaction(
            txn_type="income",
            txn_date=parsed.date,
            amount_cents=int(round(float(parsed.amount) * 100)),
            category=parsed.category,
            description=parsed.description,
            created_by_id=user.id,
            source=parsed.source or None,
        )
        if result.success:
            flash(request, "success", "Income recorded successfully!")
            return RedirectResponse(url="/admin/finance", status_code=303)
        flash(request, "error", result.message)
    flash_form_errors(request, errors)
    return render(request, "admin/create_income.html", {"form": form}, user=user, status_code=422)


@router.get("/finance/statement", name="admin.financial_statement", dependencies=[require_perms("finance.report")])
def financial_statement_page(request: Request, user: CurrentUser):
    today = date.today()
    start_date = get_membership_year_start(today)
    form = _statement_form_view(values={"start_date": start_date, "end_date": today})
    return render(request, "admin/financial_statement.html", {"form": form, "statement": None}, user=user)


@router.post("/finance/statement", name="admin.financial_statement_post", dependencies=[require_perms("finance.report")])
def financial_statement_store(request: Request, user: CurrentUser, form_data: CsrfFormData):
    parsed, errors, values = parse_form(FinancialStatementForm, form_data)
    form = _statement_form_view(values=values, errors=errors)
    if parsed:
        if parsed.end_date < parsed.start_date:
            flash(request, "error", "End date must be after start date.")
            return render(request, "admin/financial_statement.html", {"form": form, "statement": None}, user=user)
        statement = finance.generate_statement(parsed.start_date, parsed.end_date)
        return render(request, "admin/financial_statement.html", {"form": form, "statement": statement}, user=user)
    flash_form_errors(request, errors)
    return render(request, "admin/financial_statement.html", {"form": form, "statement": None}, user=user, status_code=422)


@router.get("/finance/statement/pdf", name="admin.financial_statement_pdf", dependencies=[require_perms("finance.report")])
def financial_statement_pdf(request: Request, user: CurrentUser):
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
def edit_transaction_page(transaction_id: int, request: Request, user: CurrentUser):
    transaction = finance.get_transaction_by_id(transaction_id)
    if not transaction:
        return render(request, "errors/404.html", user=user, status_code=404)
    form = _transaction_form_view(transaction)
    return render(request, "admin/edit_transaction.html", {"transaction": transaction, "form": form}, user=user)


@router.post("/finance/{transaction_id}/edit", name="admin.edit_transaction_post", dependencies=[require_perms("finance.update")])
def edit_transaction_store(transaction_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    transaction = finance.get_transaction_by_id(transaction_id)
    if not transaction:
        return render(request, "errors/404.html", user=user, status_code=404)
    if transaction.type == "expense":
        parsed_expense, errors, values = parse_form(ExpenseForm, form_data)
        form = _transaction_form_view(transaction, values=values, errors=errors)
        if parsed_expense:
            result = finance.update_transaction(
                transaction=transaction,
                txn_date=parsed_expense.date,
                amount_cents=int(round(float(parsed_expense.amount) * 100)),
                category=parsed_expense.category,
                description=parsed_expense.description,
                receipt_reference=parsed_expense.receipt_reference or None,
            )
            if result.success:
                flash(request, "success", "Transaction updated successfully!")
                return RedirectResponse(url="/admin/finance", status_code=303)
            flash(request, "error", result.message or "An error occurred while updating the transaction.")
    else:
        parsed_income, errors, values = parse_form(IncomeForm, form_data)
        form = _transaction_form_view(transaction, values=values, errors=errors)
        if parsed_income:
            result = finance.update_transaction(
                transaction=transaction,
                txn_date=parsed_income.date,
                amount_cents=int(round(float(parsed_income.amount) * 100)),
                category=parsed_income.category,
                description=parsed_income.description,
                source=parsed_income.source or None,
            )
            if result.success:
                flash(request, "success", "Transaction updated successfully!")
                return RedirectResponse(url="/admin/finance", status_code=303)
            flash(request, "error", result.message or "An error occurred while updating the transaction.")
    flash_form_errors(request, errors)
    return render(
        request,
        "admin/edit_transaction.html",
        {"transaction": transaction, "form": form},
        user=user,
        status_code=422,
    )


@router.post("/finance/{transaction_id}/delete", name="admin.delete_transaction", dependencies=[require_perms("finance.delete")])
def delete_transaction(transaction_id: int, request: Request, user: CurrentUser, form_data: CsrfFormData):
    result = finance.delete_transaction(transaction_id)
    flash(
        request,
        "success" if result.success else "error",
        result.message or ("Transaction deleted." if result.success else "Error deleting transaction."),
    )
    return RedirectResponse(url="/admin/finance", status_code=303)
