"""Admin routes for financial transaction management."""

from flask import Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.forms.admin_forms import ExpenseForm, FinancialStatementForm, IncomeForm
from app.services import FinanceService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/finance")
@permission_required("finance.read")
def finance():
    """List all financial transactions."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    if per_page not in (10, 20, 50, 100):
        per_page = 20
    pagination = FinanceService.get_all_transactions_paginated(page=page, per_page=per_page)
    return render_template("admin/finance.html", transactions=pagination.items, pagination=pagination, per_page=per_page)


@bp.get("/finance/expense/create")
@permission_required("finance.create")
def create_expense():
    """Display expense creation form."""
    return render_template("admin/create_expense.html", form=ExpenseForm())


@bp.post("/finance/expense/create")
@permission_required("finance.create")
def create_expense_post():
    """Handle expense creation form submission."""
    form = ExpenseForm()

    if form.validate_on_submit():
        transaction, error = FinanceService.create_transaction(
            txn_type="expense",
            txn_date=form.date.data,
            amount=float(form.amount.data),
            category=form.category.data,
            description=form.description.data,
            created_by_id=current_user.id,
            receipt_reference=form.receipt_reference.data or None,
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_expense.html", form=form)

        flash("Expense recorded successfully!", "success")
        return redirect(url_for("admin.finance"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_expense.html", form=form)


@bp.get("/finance/income/create")
@permission_required("finance.create")
def create_income():
    """Display income creation form."""
    return render_template("admin/create_income.html", form=IncomeForm())


@bp.post("/finance/income/create")
@permission_required("finance.create")
def create_income_post():
    """Handle income creation form submission."""
    form = IncomeForm()

    if form.validate_on_submit():
        transaction, error = FinanceService.create_transaction(
            txn_type="income",
            txn_date=form.date.data,
            amount=float(form.amount.data),
            category=form.category.data,
            description=form.description.data,
            created_by_id=current_user.id,
            source=form.source.data or None,
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_income.html", form=form)

        flash("Income recorded successfully!", "success")
        return redirect(url_for("admin.finance"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_income.html", form=form)


@bp.get("/finance/<int:transaction_id>/edit")
@permission_required("finance.update")
def edit_transaction(transaction_id):
    """Display transaction edit form."""
    transaction = FinanceService.get_transaction_by_id(transaction_id)
    if not transaction:
        abort(404)

    if transaction.type == "expense":
        form = ExpenseForm(obj=transaction)
        form.amount.data = transaction.amount
    else:
        form = IncomeForm(obj=transaction)
        form.amount.data = transaction.amount

    return render_template(
        "admin/edit_transaction.html",
        transaction=transaction,
        form=form,
    )


@bp.post("/finance/<int:transaction_id>/edit")
@permission_required("finance.update")
def edit_transaction_post(transaction_id):
    """Handle transaction edit form submission."""
    transaction = FinanceService.get_transaction_by_id(transaction_id)
    if not transaction:
        abort(404)

    if transaction.type == "expense":
        form = ExpenseForm(obj=transaction)
    else:
        form = IncomeForm(obj=transaction)

    if form.validate_on_submit():
        kwargs = dict(
            transaction=transaction,
            txn_date=form.date.data,
            amount=float(form.amount.data),
            category=form.category.data,
            description=form.description.data,
        )
        if transaction.type == "expense":
            kwargs["receipt_reference"] = form.receipt_reference.data or None
        else:
            kwargs["source"] = form.source.data or None

        success, error = FinanceService.update_transaction(**kwargs)

        if not success:
            flash(error or "An error occurred while updating the transaction.", "error")
            return render_template(
                "admin/edit_transaction.html",
                transaction=transaction,
                form=form,
            )

        flash("Transaction updated successfully!", "success")
        return redirect(url_for("admin.finance"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template(
        "admin/edit_transaction.html",
        transaction=transaction,
        form=form,
    )


@bp.post("/finance/<int:transaction_id>/delete")
@permission_required("finance.delete")
def delete_transaction(transaction_id):
    """Delete a financial transaction."""
    success, error = FinanceService.delete_transaction(transaction_id)

    if not success:
        flash(error or "An error occurred while deleting the transaction.", "error")
    else:
        flash("Transaction deleted successfully!", "success")

    return redirect(url_for("admin.finance"))


@bp.get("/finance/statement")
@permission_required("finance.report")
def financial_statement():
    """Display the financial statement form."""
    form = FinancialStatementForm()
    return render_template("admin/financial_statement.html", form=form, statement=None)


@bp.post("/finance/statement")
@permission_required("finance.report")
def financial_statement_post():
    """Generate and display a financial statement."""
    form = FinancialStatementForm()

    if form.validate_on_submit():
        if form.end_date.data < form.start_date.data:
            flash("End date must be after start date.", "error")
            return render_template("admin/financial_statement.html", form=form, statement=None)

        statement = FinanceService.generate_statement(
            start_date=form.start_date.data,
            end_date=form.end_date.data,
        )
        return render_template("admin/financial_statement.html", form=form, statement=statement)

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/financial_statement.html", form=form, statement=None)


@bp.get("/finance/statement/pdf")
@permission_required("finance.report")
def financial_statement_pdf():
    """Download a financial statement as a PDF."""
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not start_date_str or not end_date_str:
        flash("Please provide start and end dates.", "error")
        return redirect(url_for("admin.financial_statement"))

    from datetime import date

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        flash("Invalid date format.", "error")
        return redirect(url_for("admin.financial_statement"))

    if end_date < start_date:
        flash("End date must be after start date.", "error")
        return redirect(url_for("admin.financial_statement"))

    statement = FinanceService.generate_statement(start_date=start_date, end_date=end_date)
    pdf_bytes = bytes(FinanceService.generate_statement_pdf(statement))

    filename = f"financial_statement_{start_date_str}_to_{end_date_str}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
